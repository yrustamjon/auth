from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from apps.common.models import Organization, Users
from apps.biometrik.models import FingerprintSession

@override_settings(PUBLIC_SITE_URL='http://localhost:5173')
class FrontendFingerprintOptionsTests(TestCase):
    def setUp(self):
        org=Organization.objects.create(name='Phone',slug='phone-react')
        user=Users.objects.create(organization=org,fio='Test',username='test',lavozim='Staff')
        self.session=FingerprintSession.objects.create(user=user,challenge=b'x'*32)

    def test_options_supply_server_challenge_and_public_origin(self):
        response=self.client.get(f'/api/fingerprint/phone/options/{self.session.session_id}/')
        self.assertEqual(response.status_code,200,response.content)
        data=response.json()
        self.assertEqual(data['rp_id'],'localhost')
        self.assertEqual(data['origin'],'http://localhost:5173')
        self.assertEqual(data['username'],'test')
        self.assertTrue(data['challenge'])

    def test_expired_or_completed_ceremony_has_no_options(self):
        url=f'/api/fingerprint/phone/options/{self.session.session_id}/'
        FingerprintSession.objects.filter(pk=self.session.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get(url).status_code,410)
        FingerprintSession.objects.filter(pk=self.session.pk).update(status='completed',expires_at=timezone.now()+timedelta(minutes=1))
        self.assertEqual(self.client.get(url).status_code,410)
