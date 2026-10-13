import uuid
import json
from datetime import timedelta
from django.test import TestCase, RequestFactory
from django.utils import timezone
from apps.common.models import Organization, Device, AdminUser
from apps.agent.telemetry import ingest, detect_missing
from apps.agent.models import AgentHealth, AgentEvent


class AgentTelemetryTests(TestCase):
    def setUp(self):
        self.org=Organization.objects.create(name='Telemetry',slug='telemetry')
        self.device=Device.objects.create(organization=self.org,pc_id='PC-T',location='Office',enrollment_status='agent_enrolled')
        self.request=RequestFactory().post('/api/agent/telemetry/',REMOTE_ADDR='192.0.2.10')
        self.request.bioguard_device=self.device

    def report(self,events=None):
        return ingest(self.request,{'events':events or [],'state':'running'})

    def test_signed_device_scope_and_duplicate_event(self):
        event={'id':str(uuid.uuid4()),'kind':'agent_started','reported_at':timezone.now().isoformat(),'details':{'pid':123,'os_user':'Ali','token':'SECRET'}}
        self.report([event]);self.report([event])
        row=AgentEvent.objects.get(kind='agent_started')
        self.assertEqual(row.device_snapshot['pc_id'],'PC-T')
        self.assertEqual(row.ip_address,'192.0.2.10')
        self.assertNotIn('token',row.details)
        self.assertEqual(AgentHealth.objects.get(device=self.device).state,'running')

    def test_missing_connection_is_logged_once_without_claiming_user_killed_agent(self):
        self.report()
        AgentHealth.objects.filter(device=self.device).update(last_heartbeat=timezone.now()-timedelta(minutes=5))
        detect_missing(self.org.pk);detect_missing(self.org.pk)
        self.assertEqual(AgentEvent.objects.filter(kind='connection_lost').count(),1)
        self.assertEqual(AgentEvent.objects.get(kind='connection_lost').ip_address,'192.0.2.10')
        self.report()
        self.assertEqual(AgentEvent.objects.filter(kind='connection_restored').count(),1)

    def test_reported_exit_does_not_become_false_connection_loss(self):
        ingest(self.request,{'events':[{'id':str(uuid.uuid4()),'kind':'agent_exited','details':{'reason':'prerelease_exit'}}],'state':'stopped'})
        AgentHealth.objects.filter(device=self.device).update(last_heartbeat=timezone.now()-timedelta(minutes=5))
        detect_missing(self.org.pk)
        self.assertFalse(AgentEvent.objects.filter(kind='connection_lost').exists())

    def test_invalid_batch_does_not_partially_commit(self):
        with self.assertRaises(ValueError):
            self.report([{'id':str(uuid.uuid4()),'kind':'agent_started'},{'id':'invalid','kind':'agent_started'}])
        self.assertFalse(AgentEvent.objects.exists())

    def test_admin_events_are_workspace_scoped(self):
        self.report([{'id':str(uuid.uuid4()),'kind':'previous_exit_unconfirmed'}])
        other=Organization.objects.create(name='Other',slug='telemetry-other')
        AgentEvent.objects.create(organization=other,device_key=999,kind='connection_lost',device_snapshot={'pc_id':'OTHER'})
        user=AdminUser.objects.create_user('telemetry-admin','password',organization=self.org)
        self.client.force_login(user)
        session=self.client.session;session['panel']='admin';session['current_org_id']=self.org.pk;session.save()
        response=self.client.get('/api/agent-events/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()['events']),1)
        self.assertEqual(response.json()['events'][0]['device_pc_id'],'PC-T')

    def test_unsigned_request_cannot_report_a_device_event(self):
        response=self.client.post('/api/agent/telemetry/',{'state':'running','events':[]},content_type='application/json')
        self.assertEqual(response.status_code,401)
        self.assertFalse(AgentHealth.objects.exists())

    def test_signed_heartbeat_uses_verified_device(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from apps.agent.tests import headers
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.device.cert='telemetry-cert'
        self.device.device_public_key=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        self.device.save()
        path='/api/agent/telemetry/'
        body=json.dumps({'device_uuid':self.device.pc_id,'state':'running','events':[]}).encode()
        response=self.client.post(path,body,content_type='application/json',**headers(key,'POST',path,body,device=self.device.pc_id,certificate=self.device.cert))
        self.assertEqual(response.status_code,200,response.content)
        self.assertTrue(AgentHealth.objects.filter(device=self.device).exists())

    def test_authorized_pause_suppresses_missing_alert_and_records_actor(self):
        self.report()
        user=AdminUser.objects.create_user('pause-admin','password',organization=self.org)
        self.client.force_login(user)
        session=self.client.session;session['current_org_id']=self.org.pk;session.save()
        response=self.client.post(f'/api/devices/{self.device.pk}/pause-permission/',{'minutes':15,'reason':'Texnik xizmat'},content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(AgentEvent.objects.get(kind='pause_authorized').actor,user.username)
        AgentHealth.objects.filter(device=self.device).update(last_heartbeat=timezone.now()-timedelta(minutes=5))
        detect_missing(self.org.pk)
        self.assertFalse(AgentEvent.objects.filter(kind='connection_lost').exists())
        AgentHealth.objects.filter(device=self.device).update(pause_until=timezone.now()-timedelta(seconds=1))
        detect_missing(self.org.pk);detect_missing(self.org.pk)
        self.assertEqual(AgentEvent.objects.filter(kind='pause_expired').count(),1)
        self.assertEqual(AgentEvent.objects.filter(kind='connection_lost').count(),1)

    def test_agent_cannot_forge_administrator_permission_event(self):
        with self.assertRaises(ValueError):self.report([{'id':str(uuid.uuid4()),'kind':'pause_authorized'}])
        self.assertFalse(AgentEvent.objects.exists())

    def test_other_workspace_cannot_grant_pause(self):
        other=Organization.objects.create(name='Other',slug='other-pause')
        user=AdminUser.objects.create_user('other-pause-admin','password',organization=other)
        self.client.force_login(user)
        session=self.client.session;session['current_org_id']=other.pk;session.save()
        response=self.client.post(f'/api/devices/{self.device.pk}/pause-permission/',{'minutes':15,'reason':'Test'},content_type='application/json')
        self.assertEqual(response.status_code,404)
        self.assertFalse(AgentEvent.objects.filter(kind='pause_authorized').exists())

    def test_device_picker_includes_devices_before_first_heartbeat(self):
        user=AdminUser.objects.create_user('device-picker-admin','password',organization=self.org)
        self.client.force_login(user)
        session=self.client.session;session['current_org_id']=self.org.pk;session.save()
        other=Organization.objects.create(name='Other',slug='other-picker')
        Device.objects.create(organization=other,pc_id='HIDDEN',location='Other')
        response=self.client.get('/api/agent-events/')
        self.assertEqual(response.status_code,200)
        devices=response.json()['devices']
        self.assertEqual([device['id'] for device in devices],[self.device.pk])
        self.assertEqual(devices[0]['state'],'not_reporting')
        self.assertIsNone(devices[0]['last_heartbeat'])
        self.assertFalse(AgentHealth.objects.exists())
