import json
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from apps.common.models import AdminUser, Device, Organization


class DevicePlatformApiTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Platform test organization", slug="platform-test-organization"
        )
        self.admin = AdminUser.objects.create_user(
            username="platform-admin",
            password="test-password",
            organization=self.organization,
        )
        self.client.force_login(self.admin)
        session = self.client.session
        session["current_org_id"] = self.organization.id
        session.save()

    def _create_device(self, **overrides):
        payload = {
            "pc_id": "device-001",
            "location": "Office",
            "license": "WINDOWS-LICENSE",
        }
        payload.update(overrides)
        return self.client.post(
            "/api/devices",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_legacy_device_create_defaults_to_windows_and_list_exposes_platform(self):
        response = self._create_device()

        self.assertEqual(response.status_code, 201)
        device = Device.objects.get(pc_id="device-001")
        self.assertEqual(device.platform, "windows")
        devices = self.client.get("/api/devices").json()
        self.assertEqual(devices[0]["platform"], "windows")

    def test_device_create_preserves_selected_macos_platform(self):
        response = self._create_device(pc_id="mac-001", platform="macos")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.get(pc_id="mac-001").platform, "macos")

    def test_invalid_platform_is_rejected_without_creating_a_device(self):
        response = self._create_device(platform="android")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid platform")
        self.assertFalse(Device.objects.exists())


class DevicePlatformUiContractTests(TestCase):
    def test_devices_page_has_platform_filter_and_add_form_selector(self):
        template = (Path(settings.BASE_DIR) / "templates" / "devices.html").read_text()
        script = (Path(settings.BASE_DIR) / "static" / "js" / "devices.js").read_text()

        self.assertIn('id="platformFilter"', template)
        self.assertIn('<option value="windows">Windows</option>', template)
        self.assertIn('<option value="macos">macOS</option>', template)
        self.assertIn('<option value="linux">Linux</option>', template)
        self.assertIn('id="platform"', template)
        self.assertIn("platformFilter", script)
        self.assertIn("device.platform", script)
        self.assertIn('platform:          document.getElementById("platform").value', script)
