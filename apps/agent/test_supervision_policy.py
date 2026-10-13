from django.test import TestCase,RequestFactory
from django.utils import timezone
from datetime import timedelta
from apps.common.models import Organization,Device
from apps.agent.models import AgentHealth
from apps.agent.telemetry import SupervisionPolicyView,ingest


class SupervisionPolicyTests(TestCase):
    def setUp(self):
        self.org=Organization.objects.create(name='Guard',slug='guard')
        self.device=Device.objects.create(organization=self.org,pc_id='GUARD',location='Test')
        self.factory=RequestFactory()

    def test_verified_device_receives_only_its_pause_permission(self):
        until=timezone.now()+timedelta(minutes=15)
        AgentHealth.objects.create(device=self.device,last_heartbeat=timezone.now(),pause_until=until)
        request=self.factory.get('/api/agent/supervision/');request.bioguard_device=self.device
        response=SupervisionPolicyView.as_view()(request)
        self.assertTrue(response.data['allowed']);self.assertEqual(response.data['pause_until'],until)

    def test_unsigned_policy_request_is_rejected(self):
        response=SupervisionPolicyView.as_view()(self.factory.get('/api/agent/supervision/'))
        self.assertEqual(response.status_code,401)

    def test_supervisor_heartbeat_does_not_hide_missing_agent(self):
        old=timezone.now()-timedelta(minutes=5)
        AgentHealth.objects.create(device=self.device,last_heartbeat=old,state='running')
        request=self.factory.post('/api/agent/telemetry/');request.bioguard_device=self.device
        ingest(request,{'reporter':'supervisor','state':'running','events':[]})
        health=AgentHealth.objects.get(device=self.device)
        self.assertEqual(health.last_heartbeat,old);self.assertTrue(health.loss_reported)
