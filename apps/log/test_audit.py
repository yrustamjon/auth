from django.test import TestCase, RequestFactory, override_settings
from unittest.mock import patch
from apps.common.models import Organization, Users, Device, AccessLogs, AdminUser
from apps.agent.models import AgentSession
from apps.log.audit import write_access_log, serialize_log, request_snapshot


class AuditTests(TestCase):
    def setUp(self):
        self.org=Organization.objects.create(name='Audit',slug='audit')
        self.user=Users.objects.create(organization=self.org,username='ali',fio='Ali',lavozim='Owner')
        self.device=Device.objects.create(organization=self.org,pc_id='PC-1',platform='windows',location='Office',identifiers={'machine_guid':'machine-1'},last_ip='192.0.2.10')
        self.session=AgentSession.objects.create(user=self.user,device=self.device)
        self.request=RequestFactory().post('/api/face/phone/submit/example/',REMOTE_ADDR='192.0.2.20',HTTP_USER_AGENT='Mobile browser',HTTP_X_FORWARDED_FOR='203.0.113.9')

    def test_snapshot_survives_device_changes_and_deletion(self):
        log=write_access_log(self.session,self.device,True,'Verified',request=self.request,similarity=0.92,client_info={'language':'uz','timezone':'Asia/Tashkent','screen':{'width':390,'height':844},'token':'secret'})
        self.device.pc_id='CHANGED';self.device.save()
        self.user.fio='Changed';self.user.save()
        self.device.delete();self.user.delete();log.refresh_from_db()
        data=serialize_log(log)
        self.assertEqual(data['device_pc_id'],'PC-1')
        self.assertEqual(data['user_fio'],'Ali')
        self.assertEqual(data['ip_address'],'192.0.2.20')
        self.assertEqual(data['similarity'],0.92)
        self.assertEqual(data['source'],'mobile_web')
        self.assertEqual(data['device_snapshot']['identifiers']['machine_guid'],'machine-1')
        self.assertNotIn('token',data['request_context']['client'])
        self.assertEqual(data['request_context']['client']['screen']['width'],390)

    def test_untrusted_forwarded_ip_is_not_used(self):
        self.assertEqual(request_snapshot(self.request)['ip_address'],'192.0.2.20')

    @override_settings(AUDIT_TRUSTED_PROXY_IPS=['192.0.2.20'])
    def test_trusted_proxy_uses_validated_forwarded_ip(self):
        self.assertEqual(request_snapshot(self.request)['ip_address'],'203.0.113.9')

    def test_legacy_log_fallback(self):
        log=AccessLogs.objects.create(organization=self.org,user=self.user,device=self.device,success=False,cause='similarity=0.5000')
        self.assertEqual(serialize_log(log)['similarity'],0.5)
        self.assertEqual(serialize_log(log)['device_pc_id'],'PC-1')
        self.assertIsNone(serialize_log(log)['ip_address'])

    def test_list_is_scoped_and_returns_snapshot(self):
        write_access_log(self.session,self.device,True,'Verified',request=self.request,similarity=0.91)
        other=Organization.objects.create(name='Other',slug='other-audit')
        AccessLogs.objects.create(organization=other,user=self.user,device=self.device,success=False)
        admin=AdminUser.objects.create_user('audit-admin','password',organization=self.org)
        self.client.force_login(admin)
        session=self.client.session;session['current_org_id']=self.org.id;session['panel']='admin';session.save()
        response=self.client.get('/api/access-logs')
        self.assertEqual(response.status_code,200)
        logs=response.json()['logs'];self.assertEqual(len(logs),1)
        self.assertEqual(logs[0]['ip_address'],'192.0.2.20')

    def test_phone_logs_the_session_device_and_browser_not_first_org_device(self):
        target=Device.objects.create(organization=self.org,pc_id='PC-2',platform='linux',location='Lab')
        self.session.device=target
        self.session.request_context={'ip_address':'192.0.2.10','user_agent':'Desktop agent'}
        self.session.save()
        response=self.client.post(f'/api/face/phone/submit/{self.session.session_id}/',
            {'image':'aGVsbG8=','client_info':{'language':'uz','timezone':'Asia/Tashkent'}},content_type='application/json',
            REMOTE_ADDR='192.0.2.20',HTTP_USER_AGENT='Mobile browser')
        self.assertEqual(response.status_code,200)
        log=AccessLogs.objects.get()
        self.assertEqual(log.device_id,target.pk)
        self.assertEqual(log.device_snapshot['platform'],'linux')
        self.assertEqual(log.ip_address,'192.0.2.20')
        self.assertEqual(log.request_context['initiator']['ip_address'],'192.0.2.10')
        self.assertEqual(log.request_context['client']['timezone'],'Asia/Tashkent')

    @patch('apps.biometrik.webauthn_service.authenticate')
    def test_fingerprint_login_saves_request_context(self,authenticate):
        response=self.client.post(f'/api/agent/fingerprint/phone/submit/{self.session.session_id}/',
            {'client_info':{'language':'uz'}},content_type='application/json',REMOTE_ADDR='192.0.2.30')
        self.assertEqual(response.status_code,200)
        authenticate.assert_called_once()
        log=AccessLogs.objects.get()
        self.assertTrue(log.success)
        self.assertEqual(log.ip_address,'192.0.2.30')

    def test_missing_fields_and_oversized_client_values_are_bounded(self):
        context=request_snapshot(self.request,{'user_agent':'x'*3000,'screen':{'width':float('inf'),'height':True},'timezone':['invalid']})
        self.assertEqual(len(context['client']['user_agent']),1024)
        self.assertEqual(context['client']['screen'],{})
        self.assertNotIn('timezone',context['client'])
