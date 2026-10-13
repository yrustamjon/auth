from urllib.parse import urlsplit
from datetime import timedelta
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from apps.common.models import AdminUser, Organization
from apps.device.browser_enrollment import create_session, submit_identity
from apps.device.models import BrowserEnrollmentSession

@override_settings(PUBLIC_SITE_URL='http://localhost:5173')
class FrontendEnrollmentTests(TestCase):
    def setUp(self):
        self.org=Organization.objects.create(name='Example',slug='react-example')
        self.admin=AdminUser.objects.create_user('react-admin','test-password',organization=self.org)
        self.target=Client()
        self.target.get('/api/session/')
        session,url,_,_=create_session(browser_key=self.target.session.session_key,source_ip='127.0.0.1')
        self.enrollment=session
        self.token=urlsplit(url).path.rsplit('/',1)[1]
        # Submit a verified helper report using the same service as native helper.
        payload=self.target.post('/api/devices/browser-enrollment/session/',{},content_type='application/json').json()
        self.enrollment=BrowserEnrollmentSession.objects.get(pk=payload['session_id'])
        self.token=urlsplit(payload['qr_url']).path.rsplit('/',1)[1]
        submit_identity(session_id=self.enrollment.id,scan_token=payload['scan_token'],platform='linux',device_id='react-machine',identifiers={'machine_id':'react-machine','product_uuid':'react-product'},hostname='react-host')

    def claim(self,client):
        return client.post('/api/devices/browser-enrollment/claim/',{'token':self.token},content_type='application/json')

    def login(self,client,org=None):
        client.force_login(self.admin)
        state=client.session
        state['panel']='admin'
        state['current_org_id']=(org or self.org).id
        state.save()

    def test_anonymous_claim_continues_after_login_and_duplicate_approval_rejected(self):
        phone=Client()
        self.assertEqual(self.claim(phone).status_code,401)
        self.login(phone)
        response=phone.get('/api/devices/browser-enrollment/approval/')
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['enrollment']['hostname'],'react-host')
        url=f'/api/devices/browser-enrollment/session/{self.enrollment.id}/approve/'
        self.assertEqual(phone.post(url,{'location':'Office'},content_type='application/json').status_code,200)
        self.assertEqual(phone.post(url,{},content_type='application/json').status_code,409)

    def test_wrong_organization_and_expired_qr(self):
        phone=Client()
        other=Organization.objects.create(name='Other',slug='react-other')
        self.login(phone,other)
        self.assertEqual(self.claim(phone).status_code,403)
        self.login(phone)
        BrowserEnrollmentSession.objects.filter(pk=self.enrollment.id).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.claim(phone).status_code,410)

    def test_claim_requires_csrf(self):
        phone=Client(enforce_csrf_checks=True)
        self.assertEqual(self.claim(phone).status_code,403)
