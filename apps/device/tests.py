import json
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from apps.common.models import AdminUser, Device, Organization
from apps.device.models import DeviceEnrollmentSession, BrowserEnrollmentSession, BrowserEnrollmentAudit
from apps.org.models import OrgToken


class DevicePlatformApiTests(TestCase):
    def valid_public_key(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        self.activation_key=rsa.generate_private_key(public_exponent=65537, key_size=2048)
        return self.activation_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

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

    def test_macos_identifiers_are_stored_as_metadata(self):
        response = self._create_device(
            pc_id="agent-mac-id", platform="macos", license="UNKNOWN",
            identifiers={"platform_uuid": "mac-platform-uuid", "serial": "C02TEST"},
        )
        self.assertEqual(response.status_code, 201)
        device = Device.objects.get(pc_id="agent-mac-id")
        self.assertEqual(device.identifiers["serial"], "C02TEST")
        self.assertEqual(device.license, "UNKNOWN")
        self.assertEqual(self.client.get("/api/devices").json()[0]["device_id"], "agent-mac-id")

    def test_canonical_device_properties_are_writable_compatibility_aliases(self):
        device = Device.objects.create(
            organization=self.organization,
            pc_id="legacy-id",
            license="UNKNOWN",
            location="Office",
        )
        device.device_id = "canonical-id"
        device.public_key = "public-key"
        device.save()
        device.refresh_from_db()
        self.assertEqual(device.device_id, "canonical-id")
        self.assertEqual(device.pc_id, "canonical-id")
        self.assertEqual(device.public_key, "public-key")
        self.assertEqual(device.device_public_key, "public-key")

    def test_windows_identifiers_must_match_legacy_activation_fields(self):
        response = self._create_device(
            identifiers={"machine_guid": "other-guid", "product_id": "WINDOWS-LICENSE"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Device.objects.exists())

    def test_linux_registration_does_not_require_windows_license(self):
        response = self._create_device(
            pc_id="linux-agent-id", platform="linux", license=None,
            identifiers={"machine_id": "linux-machine-id", "product_uuid": "linux-product-uuid"},
        )
        self.assertEqual(response.status_code, 201)
        device = Device.objects.get(pc_id="linux-agent-id")
        self.assertEqual(device.license, "UNKNOWN")
        self.assertEqual(device.identifiers["machine_id"], "linux-machine-id")

    def test_windows_edit_updates_product_id_and_legacy_license_together(self):
        self._create_device(
            pc_id="win-guid", identifiers={"machine_guid": "win-guid", "product_id": "WINDOWS-LICENSE"}
        )
        device = Device.objects.get(pc_id="win-guid")
        response = self.client.put(
            f"/api/devices/{device.id}/",
            data=json.dumps({
                "pc_id": "win-guid", "platform": "windows", "location": "Office",
                "license": "NEW-PRODUCT-ID",
                "identifiers": {"machine_guid": "win-guid", "product_id": "NEW-PRODUCT-ID"},
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertEqual(device.license, "NEW-PRODUCT-ID")
        self.assertEqual(device.identifiers["product_id"], "NEW-PRODUCT-ID")

    def test_partial_platform_identifiers_are_rejected(self):
        response = self._create_device(
            platform="macos", pc_id="mac-id", license=None,
            identifiers={"serial": "SERIAL-ONLY"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Device.objects.exists())

    def test_windows_legacy_activation_still_matches_pc_id_and_product_id(self):
        response = self._create_device(
            pc_id="win-machine-guid", license="WIN-PRODUCT-ID",
            identifiers={"machine_guid": "win-machine-guid", "product_id": "WIN-PRODUCT-ID"},
        )
        self.assertEqual(response.status_code, 201)
        token = OrgToken.objects.create(org=self.organization)
        from apps.agent.tests import headers
        payload=json.dumps({"activation_code":token.token,"device_uuid":"win-machine-guid",
            "windows_license":"WIN-PRODUCT-ID","public_key":self.valid_public_key()}).encode()
        activation=self.client.post('/api/agent/activate/',payload,content_type='application/json',
            **headers(self.activation_key,'POST','/api/agent/activate/',payload,device='win-machine-guid',certificate='bootstrap'))
        self.assertEqual(activation.status_code, 200, activation.content)

    def test_device_keeps_neutral_lifecycle_fields_without_activating_it(self):
        self._create_device(pc_id="mac-identity", platform="macos", license=None)
        device = Device.objects.get(pc_id="mac-identity")
        self.assertEqual(device.device_id, "mac-identity")
        self.assertEqual(device.attestation_status, "not_provided")
        self.assertIsNone(device.enrolled_at)
        self.assertIsNone(device.revoked_at)
        self.assertIsNotNone(device.created_at)
        self.assertIsNotNone(device.updated_at)


class DevicePlatformUiContractTests(TestCase):
    def test_browser_approved_device_is_labeled_not_activatable_in_list(self):
        script = (Path(settings.BASE_DIR) / "static" / "js" / "devices.js").read_text()
        self.assertIn("browser_approved", script)
        self.assertIn("Agent key", script)
        self.assertIn("escapeHtml", script)

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

    def test_add_form_uses_platform_specific_identifier_help(self):
        template = (Path(settings.BASE_DIR) / "templates" / "devices.html").read_text()
        script = (Path(settings.BASE_DIR) / "static" / "js" / "devices.js").read_text()

        self.assertIn('id="licenseField"', template)
        self.assertIn('id="pcIdHint"', template)
        self.assertIn("syncPlatformFields", script)
        self.assertIn("'UNKNOWN'", script)

    def test_add_form_has_platform_specific_identifier_fields(self):
        template = (Path(settings.BASE_DIR) / "templates" / "devices.html").read_text()
        for field_id in ("machine_guid", "product_id", "platform_uuid", "serial", "machine_id", "product_uuid"):
            self.assertIn(f'id="{field_id}"', template)
        self.assertIn('id="windowsIdentifiers"', template)
        self.assertIn('id="macosIdentifiers"', template)
        self.assertIn('id="linuxIdentifiers"', template)

    def test_target_scan_polls_for_helper_identity_every_second(self):
        template = (Path(settings.BASE_DIR) / "templates" / "device_scan.html").read_text()
        self.assertIn("timer=setTimeout(poll,1000)", template)


@override_settings(PUBLIC_SITE_URL="https://public.example")
class BrowserEnrollmentTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="QR Org", slug="qr-org")
        self.other_org = Organization.objects.create(name="Other QR Org", slug="other-qr-org")
        self.admin = AdminUser.objects.create_user(
            username="qr-admin", password="test-password", organization=self.org
        )
        self.other_admin = AdminUser.objects.create_user(
            username="other-qr-admin", password="test-password", organization=self.other_org
        )
        self.target = Client()

    def create_session(self, platform="macos", device_id="TARGET-PC-01", identifiers=None):
        self.assertEqual(self.target.get("/device/scan").status_code, 200)
        response = self.target.post(
            "/api/devices/browser-enrollment/session/",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        payload = response.json()
        primary = {"windows": "machine_guid", "macos": "platform_uuid", "linux": "machine_id"}[platform]
        identity = {primary: device_id}
        identity.update(identifiers or {})
        reported = Client().post(
            f"/api/devices/browser-enrollment/session/{payload['session_id']}/identity/",
            data=json.dumps({
                "scan_token": payload["scan_token"], "platform": platform,
                "device_id": device_id, "identifiers": identity, "hostname": "target-host",
            }), content_type="application/json",
        )
        self.assertEqual(reported.status_code, 200, reported.content)
        return payload

    def phone_claim(self, payload, admin=None, org=None):
        phone = Client()
        entry = phone.get(urlsplit(payload["qr_url"]).path)
        self.assertEqual(entry.status_code, 302)
        phone.force_login(admin or self.admin)
        session = phone.session
        session["current_org_id"] = (org or self.org).id
        session.save()
        approval = phone.get("/device-enroll/approval/")
        self.assertEqual(approval.status_code, 200, approval.content)
        return phone

    def test_three_platforms_create_short_lived_hashed_qr(self):
        self.assertEqual(DeviceEnrollmentSession._meta.model_name, "deviceenrollmentsession")
        self.assertIs(BrowserEnrollmentSession, DeviceEnrollmentSession)
        for platform in ("windows", "macos", "linux"):
            payload = self.create_session(platform, device_id=f"target-{platform}")
            stored = BrowserEnrollmentSession.objects.get(pk=payload["session_id"])
            self.assertEqual(stored.platform, platform)
            self.assertEqual(stored.requested_device_id, f"target-{platform}")
            self.assertIsNotNone(stored.identity_received_at)
            self.assertIsNone(stored.organization)
            self.assertNotIn(stored.token_hash, payload["qr_url"])
            self.assertLessEqual((stored.expires_at - timezone.now()).total_seconds(), 300)
            self.assertIn("<svg", payload["qr_svg"])

    def test_display_code_is_derived_for_both_screens_and_not_stored_in_plaintext(self):
        payload = self.create_session()
        stored = BrowserEnrollmentSession.objects.get(pk=payload["session_id"])
        self.assertEqual(stored.display_code_hash, __import__("hashlib").sha256(
            payload["display_code"].encode()
        ).hexdigest())
        self.assertNotEqual(stored.display_code_hash, payload["display_code"])
        self.assertEqual(stored.session_id, stored.id)
        self.assertEqual(stored.browser_session_hash, stored.creator_session_hash)
        phone = self.phone_claim(payload)
        self.assertContains(phone.get("/device-enroll/approval/"), payload["display_code"])
        stored.refresh_from_db()
        self.assertIsNotNone(stored.claimed_at)
        self.assertEqual(stored.platform_claimed, "macos")
        self.assertEqual(stored.device_metadata["device_id"], "TARGET-PC-01")
        response = phone.post(
            f"/api/devices/browser-enrollment/session/{stored.id}/approve/"
        )
        self.assertEqual(response.status_code, 200)
        stored.refresh_from_db()
        self.assertEqual(stored.approved_by_id, self.admin.id)

    def test_admin_add_via_qr_path_preserves_previous_scanner_path(self):
        phone = Client()
        phone.force_login(self.admin)
        session = phone.session
        session["current_org_id"] = self.org.id
        session.save()
        self.assertEqual(phone.get("/devices/add/qr").status_code, 200)
        self.assertEqual(phone.get("/devices/scan-qr/").status_code, 200)

    def test_admin_scans_and_approves_one_inactive_device(self):
        payload = self.create_session(
            "linux", device_id="LINUX-MACHINE",
            identifiers={"product_uuid": "LINUX-PRODUCT"},
        )
        self.assertFalse(Device.objects.exists())
        phone = self.phone_claim(payload)
        self.assertContains(phone.get("/device-enroll/approval/"), "LINUX-MACHINE")
        url = f"/api/devices/browser-enrollment/session/{payload['session_id']}/approve/"
        first = phone.post(url)
        self.assertEqual(first.status_code, 200, first.content)
        device = Device.objects.get(organization=self.org)
        self.assertEqual(device.platform, "linux")
        self.assertEqual(device.pc_id, "LINUX-MACHINE")
        self.assertEqual(device.identifiers["machine_id"], "LINUX-MACHINE")
        self.assertEqual(device.enrollment_status, "browser_approved")
        self.assertFalse(device.is_active)
        self.assertIsNone(device.device_public_key)
        self.assertEqual(phone.post(url).status_code, 409)
        self.assertEqual(Device.objects.count(), 1)
        self.assertEqual(self.target.get(
            f"/api/devices/browser-enrollment/session/{payload['session_id']}/"
        ).json()["status"], "approved")

    def test_admin_approval_persists_explicit_location(self):
        payload = self.create_session(
            "linux", device_id="located-machine",
            identifiers={"product_uuid": "located-product"},
        )
        phone = self.phone_claim(payload)
        response = phone.post(
            f"/api/devices/browser-enrollment/session/{payload['session_id']}/approve/",
            data=json.dumps({"location": "Tashkent office"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(Device.objects.get().location, "Tashkent office")

    def test_expired_qr_and_wrong_browser_cannot_resolve(self):
        payload = self.create_session()
        url = f"/api/devices/browser-enrollment/session/{payload['session_id']}/"
        self.assertEqual(Client().get(url).status_code, 404)
        BrowserEnrollmentSession.objects.filter(pk=payload["session_id"]).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertEqual(self.target.get(url).json()["status"], "expired")
        self.assertFalse(Device.objects.exists())

    def test_claimed_qr_cannot_move_to_another_organization(self):
        payload = self.create_session()
        self.phone_claim(payload)
        other = Client()
        other.get(urlsplit(payload["qr_url"]).path)
        other.force_login(self.other_admin)
        session = other.session
        session["current_org_id"] = self.other_org.id
        session.save()
        self.assertEqual(other.get("/device-enroll/approval/").status_code, 403)
        self.assertFalse(Device.objects.exists())

    def test_first_authorized_admin_binds_anonymous_qr_to_organization(self):
        payload = self.create_session()
        other = Client()
        other.get(urlsplit(payload["qr_url"]).path)
        other.force_login(self.other_admin)
        session = other.session
        session["current_org_id"] = self.other_org.id
        session.save()
        self.assertEqual(other.get("/device-enroll/approval/").status_code, 200)
        stored = BrowserEnrollmentSession.objects.get(pk=payload["session_id"])
        self.assertEqual(stored.organization_id, self.other_org.id)
        self.assertEqual(stored.claimed_by_id, self.other_admin.id)

    def test_duplicate_device_is_rejected_at_approval(self):
        Device.objects.create(
            organization=self.org, pc_id="TARGET-PC-01", platform="macos",
            location="Office", license="UNKNOWN",
        )
        payload = self.create_session("macos")
        phone = self.phone_claim(payload)
        response = phone.post(
            f"/api/devices/browser-enrollment/session/{payload['session_id']}/approve/"
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Device.objects.filter(organization=self.org).count(), 1)
        self.assertEqual(BrowserEnrollmentSession.objects.get(pk=payload["session_id"]).status, "pending")

    def test_browser_cannot_supply_unverified_identifiers_directly(self):
        self.target.get("/device/scan")
        response = self.target.post(
            "/api/devices/browser-enrollment/session/",
            data=json.dumps({"platform": "linux", "device_id": "fake-machine"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(BrowserEnrollmentSession.objects.exists())

    def test_reject_cancel_and_audit_do_not_create_devices(self):
        payload = self.create_session()
        phone = self.phone_claim(payload)
        rejected = phone.post(
            f"/api/devices/browser-enrollment/session/{payload['session_id']}/reject/"
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertFalse(Device.objects.exists())
        self.assertTrue(BrowserEnrollmentAudit.objects.filter(event="REJECTED").exists())
        second = self.create_session("windows")
        cancelled = self.target.post(
            f"/api/devices/browser-enrollment/session/{second['session_id']}/cancel/"
        )
        self.assertEqual(cancelled.status_code, 200)

    def test_qr_scanner_is_available_only_to_device_admin(self):
        self.assertEqual(self.target.get("/devices/scan-qr/").status_code, 302)
        phone = Client()
        phone.force_login(self.admin)
        session = phone.session
        session["current_org_id"] = self.org.id
        session.save()
        response = phone.get("/devices/scan-qr/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "html5-qrcode")
        self.assertContains(response, "/device-enroll/")

    def test_qr_scanner_accepts_configured_public_origin_and_preserves_full_url(self):
        phone = Client()
        phone.force_login(self.admin)
        session = phone.session
        session["current_org_id"] = self.org.id
        session.save()
        response = phone.get("/devices/scan-qr/")
        self.assertContains(response, "public.example")
        self.assertContains(response, "location.assign(url.href)")
        self.assertContains(response, "allowedOrigins")

    def test_approval_page_has_result_popup_navigation(self):
        payload = self.create_session()
        phone = self.phone_claim(payload)
        response = phone.get("/device-enroll/approval/")
        self.assertContains(response, 'id="approvalModal"')
        self.assertContains(response, "QR scannerga qaytish")
        self.assertContains(response, "Devices listga qaytish")

    def test_create_is_rate_limited(self):
        for _ in range(5):
            self.create_session()
        response = self.target.post(
            "/api/devices/browser-enrollment/session/",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 429)

    def test_qr_approval_requires_csrf(self):
        payload = self.create_session()
        phone = Client(enforce_csrf_checks=True)
        phone.get(urlsplit(payload["qr_url"]).path)
        phone.force_login(self.admin)
        session = phone.session
        session["current_org_id"] = self.org.id
        session.save()
        phone.get("/device-enroll/approval/")
        response = phone.post(
            f"/api/devices/browser-enrollment/session/{payload['session_id']}/approve/"
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Device.objects.exists())

    def test_browser_approved_device_cannot_be_activated_via_legacy_paths(self):
        payload = self.create_session()
        phone = self.phone_claim(payload)
        phone.post(f"/api/devices/browser-enrollment/session/{payload['session_id']}/approve/")
        device = Device.objects.get(organization=self.org)
        admin = Client()
        admin.force_login(self.admin)
        session = admin.session
        session["current_org_id"] = self.org.id
        session.save()
        self.assertEqual(admin.patch(
            f"/api/devices/{device.id}/",
            data=json.dumps({"is_active": True}), content_type="application/json",
        ).status_code, 409)
        self.assertEqual(admin.put(
            f"/api/devices/{device.id}/",
            data=json.dumps({"is_active": True, "device_public_key": "fake-key"}),
            content_type="application/json",
        ).status_code, 409)
        token = OrgToken.objects.create(org=self.org)
        self.assertEqual(self.target.post(
            "/api/agent/activate/", data=json.dumps({
                "activation_code": token.token, "device_uuid": device.pc_id,
                "windows_license": "UNKNOWN", "public_key": "fake-key",
            }), content_type="application/json",
        ).status_code, 400)
        self.assertEqual(self.target.post(
            "/api/agent/check-pc/", data=json.dumps({
                "device_uuid": device.pc_id, "windows_license": "UNKNOWN",
            }), content_type="application/json",
        ).status_code, 401)
        device.refresh_from_db()
        self.assertFalse(device.is_active)
        self.assertIsNone(device.device_public_key)
        self.assertFalse(OrgToken.objects.get(pk=token.pk).is_used)

    def test_cleanup_expires_old_pending_sessions(self):
        payload = self.create_session()
        BrowserEnrollmentSession.objects.filter(pk=payload["session_id"]).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        call_command("cleanup_browser_enrollment_sessions")
        stored = BrowserEnrollmentSession.objects.get(pk=payload["session_id"])
        self.assertEqual(stored.status, "expired")
        self.assertTrue(BrowserEnrollmentAudit.objects.filter(
            session_id=stored.id, event="EXPIRED"
        ).exists())


@override_settings(PUBLIC_SITE_URL="https://public.example")
class NativeRegistrationScanTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Native Scan Org", slug="native-scan-org")
        self.admin = AdminUser.objects.create_user(
            username="native-scan-admin", password="test-password", organization=self.org
        )
        self.target = Client()

    def test_scan_starts_without_manual_pc_fields_and_waits_for_helper(self):
        response = self.target.get("/device/scan")
        self.assertContains(response, 'id="scan"')
        self.assertNotContains(response, 'id="deviceId"')
        created = self.target.post(
            "/api/devices/browser-enrollment/session/", data="{}", content_type="application/json"
        )
        self.assertEqual(created.status_code, 201, created.content)
        payload = created.json()
        self.assertEqual(payload["status"], "pending")
        self.assertFalse(payload["identity_ready"])
        self.assertTrue(payload["scan_token"])
        self.assertFalse(Device.objects.exists())

    def test_helper_identifies_pc_before_admin_can_approve(self):
        self.target.get("/device/scan")
        payload = self.target.post(
            "/api/devices/browser-enrollment/session/", data="{}", content_type="application/json"
        ).json()
        identity_url = f"/api/devices/browser-enrollment/session/{payload['session_id']}/identity/"
        early_phone = Client()
        early_phone.get(urlsplit(payload["qr_url"]).path)
        early_phone.force_login(self.admin)
        session = early_phone.session
        session["current_org_id"] = self.org.id
        session.save()
        self.assertEqual(early_phone.get("/device-enroll/approval/").status_code, 409)
        wrong = Client().post(identity_url, data=json.dumps({
            "scan_token": "wrong", "platform": "linux", "device_id": "linux-machine",
            "identifiers": {"machine_id": "linux-machine"},
        }), content_type="application/json")
        self.assertEqual(wrong.status_code, 403)
        identified = Client().post(identity_url, data=json.dumps({
            "scan_token": payload["scan_token"], "platform": "linux",
            "device_id": "linux-machine", "identifiers": {
                "machine_id": "linux-machine", "product_uuid": "linux-product"
            }, "hostname": "office-linux",
        }), content_type="application/json")
        self.assertEqual(identified.status_code, 200, identified.content)
        self.assertEqual(Client().post(identity_url, data=json.dumps({
            "scan_token": payload["scan_token"], "platform": "linux",
            "device_id": "linux-machine", "identifiers": {"machine_id": "linux-machine"},
        }), content_type="application/json").status_code, 409)
        phone = Client()
        phone.get(urlsplit(payload["qr_url"]).path)
        phone.force_login(self.admin)
        session = phone.session
        session["current_org_id"] = self.org.id
        session.save()
        self.assertContains(phone.get("/device-enroll/approval/"), "linux-machine")
        self.assertContains(phone.get("/device-enroll/approval/"), "office-linux")
        self.assertFalse(Device.objects.exists())
        approved = phone.post(
            f"/api/devices/browser-enrollment/session/{payload['session_id']}/approve/"
        )
        self.assertEqual(approved.status_code, 200, approved.content)
        device = Device.objects.get(organization=self.org)
        self.assertEqual(device.pc_id, "linux-machine")
        self.assertEqual(device.identifiers["machine_id"], "linux-machine")
        self.assertFalse(device.is_active)

    def test_helper_bundle_is_bound_to_creator_and_scan_token(self):
        self.target.get("/device/scan")
        payload = self.target.post(
            "/api/devices/browser-enrollment/session/", data="{}", content_type="application/json"
        ).json()
        bundle_url = f"/api/devices/browser-enrollment/session/{payload['session_id']}/helper/macos/"
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "macos-amd64").write_bytes(b"amd64-binary")
            Path(directory, "macos-arm64").write_bytes(b"arm64-binary")
            with override_settings(DEVICE_REGISTRATION_HELPER_DIR=directory):
                self.assertEqual(Client().post(bundle_url, data=json.dumps({
                    "scan_token": payload["scan_token"]
                }), content_type="application/json").status_code, 404)
                self.assertEqual(self.target.post(bundle_url, data=json.dumps({
                    "scan_token": "wrong"
                }), content_type="application/json").status_code, 403)
                response = self.target.post(bundle_url, data=json.dumps({
                    "scan_token": payload["scan_token"]
                }), content_type="application/json")
                self.assertEqual(response.status_code, 200, response.content[:200])
                with zipfile.ZipFile(BytesIO(response.content)) as archive:
                    config = json.loads(archive.read("scan.json"))
                    self.assertEqual(config["session_id"], payload["session_id"])
                    self.assertEqual(config["scan_token"], payload["scan_token"])
                    self.assertIn("run-registration.command", archive.namelist())
                    self.assertIn("arm64", config["binary_urls"])
                    self.assertIn("--http1.1", archive.read("run-registration.command").decode())
                    self.assertIn("Press Enter", archive.read("run-registration.command").decode())

    def test_helper_bundle_can_include_only_requested_architecture(self):
        self.target.get("/device/scan")
        payload = self.target.post(
            "/api/devices/browser-enrollment/session/", data="{}", content_type="application/json"
        ).json()
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "linux-amd64").write_bytes(b"amd64-binary")
            Path(directory, "linux-arm64").write_bytes(b"arm64-binary")
            with override_settings(DEVICE_REGISTRATION_HELPER_DIR=directory):
                response = self.target.post(
                    f"/api/devices/browser-enrollment/session/{payload['session_id']}/helper/linux/",
                    data=json.dumps({"scan_token": payload["scan_token"], "architecture": "amd64"}),
                    content_type="application/json",
                )
        self.assertEqual(response.status_code, 200, response.content[:200])
        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            self.assertEqual(archive.namelist(), ["scan.json", "run-registration.sh"])
            manifest = json.loads(archive.read("scan.json"))
            self.assertEqual(manifest["architecture"], "amd64")
            self.assertTrue(manifest["binary_sha256"])

    def test_helper_binary_endpoint_streams_selected_binary(self):
        self.target.get("/device/scan")
        payload = self.target.post(
            "/api/devices/browser-enrollment/session/", data="{}", content_type="application/json"
        ).json()
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "linux-amd64").write_bytes(b"amd64-binary")
            with override_settings(DEVICE_REGISTRATION_HELPER_DIR=directory):
                response = self.target.get(
                    f"/api/devices/browser-enrollment/session/{payload['session_id']}/binary/linux/amd64/",
                    {"scan_token": payload["scan_token"]},
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"amd64-binary")
