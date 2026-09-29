"""Browser-only device pre-registration. QR possession never proves device identity."""

import hashlib
import hmac
import json
import secrets
from io import BytesIO
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlsplit
from zipfile import ZipFile, ZipInfo

import qrcode
from qrcode.image.svg import SvgPathImage
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.common.models import Device
from .models import BrowserEnrollmentAttempt, BrowserEnrollmentAudit, BrowserEnrollmentSession


class EnrollmentError(Exception):
    def __init__(self, code, status=400):
        self.code = code
        self.status = status
        super().__init__(code)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def display_code_for(session):
    material = f"browser-display-code-v1:{session.token_hash}".encode("utf-8")
    mac = hmac.new(settings.SECRET_KEY.encode("utf-8"), material, hashlib.sha256).digest()
    return f"{int.from_bytes(mac[:8], 'big') % 1_000_000:06d}"


def public_site_url():
    value = settings.PUBLIC_SITE_URL.rstrip("/")
    parsed = urlsplit(value)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise EnrollmentError("INVALID_PUBLIC_SITE_URL", 500)
    if parsed.scheme == "https" and parsed.netloc:
        return value
    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        return value
    raise EnrollmentError("PUBLIC_SITE_URL_NOT_HTTPS", 500)


def qr_svg(url):
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    code.add_data(url)
    code.make(fit=True)
    return code.make_image(image_factory=SvgPathImage).to_string(encoding="unicode")


def audit(session, event, *, actor=None, reason=""):
    BrowserEnrollmentAudit.objects.create(
        session_id=session.id,
        organization=session.organization,
        actor=actor,
        event=event,
        reason=reason,
    )


def create_session(*, browser_key, source_ip):
    base = public_site_url()
    if not browser_key:
        raise EnrollmentError("INVALID_BROWSER_SESSION")
    now = timezone.now()
    creator_hash = digest(browser_key)
    with transaction.atomic():
        BrowserEnrollmentAttempt.objects.create(
            creator_session_hash=creator_hash, source_ip=source_ip
        )
        recent = now - timedelta(minutes=5)
        if BrowserEnrollmentAttempt.objects.filter(
            creator_session_hash=creator_hash, created_at__gte=recent
        ).count() > 5:
            raise EnrollmentError("RATE_LIMITED", 429)
        if source_ip and BrowserEnrollmentAttempt.objects.filter(
            source_ip=source_ip, created_at__gte=recent
        ).count() > 60:
            raise EnrollmentError("RATE_LIMITED", 429)
        old = BrowserEnrollmentSession.objects.filter(
            creator_session_hash=creator_hash, status=BrowserEnrollmentSession.Status.PENDING
        )
        for session in old.select_for_update():
            session.status = BrowserEnrollmentSession.Status.CANCELLED
            session.resolved_at = now
            session.save(update_fields=["status", "resolved_at"])
            audit(session, "CANCELLED", reason="QR_REFRESHED")
        token = secrets.token_urlsafe(32)
        scan_token = secrets.token_urlsafe(32)
        token_hash = digest(token)
        code_material = f"browser-display-code-v1:{token_hash}".encode("utf-8")
        mac = hmac.new(settings.SECRET_KEY.encode("utf-8"), code_material, hashlib.sha256).digest()
        code = f"{int.from_bytes(mac[:8], 'big') % 1_000_000:06d}"
        session = BrowserEnrollmentSession.objects.create(
            token_hash=token_hash, scan_token_hash=digest(scan_token),
            creator_session_hash=creator_hash, location="Unknown",
            display_code_hash=digest(code),
            expires_at=now + timedelta(minutes=5),
        )
        audit(session, "CREATED")
    url = f"{base}/device-enroll/{token}"
    return session, url, qr_svg(url), scan_token


def submit_identity(*, session_id, scan_token, platform, device_id, identifiers, hostname):
    if not isinstance(scan_token, str) or not scan_token:
        raise EnrollmentError("INVALID_SCAN_TOKEN", 403)
    if platform not in Device.Platform.values:
        raise EnrollmentError("INVALID_PLATFORM")
    if not isinstance(device_id, str) or not device_id.strip() or len(device_id.strip()) > 255:
        raise EnrollmentError("INVALID_DEVICE_ID")
    if not isinstance(hostname, str) or len(hostname.strip()) > 255:
        raise EnrollmentError("INVALID_HOSTNAME")
    if not isinstance(identifiers, dict):
        raise EnrollmentError("INVALID_IDENTIFIERS")
    allowed = {
        Device.Platform.WINDOWS: {"machine_guid", "product_id"},
        Device.Platform.MACOS: {"platform_uuid", "serial"},
        Device.Platform.LINUX: {"machine_id", "product_uuid"},
    }[platform]
    primary = {
        Device.Platform.WINDOWS: "machine_guid",
        Device.Platform.MACOS: "platform_uuid",
        Device.Platform.LINUX: "machine_id",
    }[platform]
    if set(identifiers) - allowed or any(
        not isinstance(value, str) or len(value.strip()) > 255 for value in identifiers.values()
    ) or not identifiers.get(primary):
        raise EnrollmentError("INVALID_IDENTIFIERS")
    normalized = {key: value.strip() for key, value in identifiers.items() if value.strip()}
    if normalized[primary] != device_id.strip():
        raise EnrollmentError("DEVICE_ID_MISMATCH")
    with transaction.atomic():
        session = BrowserEnrollmentSession.objects.select_for_update().filter(pk=session_id).first()
        if not session or not secrets.compare_digest(session.scan_token_hash, digest(scan_token)):
            raise EnrollmentError("INVALID_SCAN_TOKEN", 403)
        expired = expire_if_needed(session)
        if not expired:
            if session.status != BrowserEnrollmentSession.Status.PENDING or session.identity_received_at:
                raise EnrollmentError("SCAN_ALREADY_COMPLETED", 409)
            session.platform = platform
            session.requested_device_id = device_id.strip()
            session.identifiers = normalized
            session.hostname = hostname.strip()
            session.identity_received_at = timezone.now()
            session.save(update_fields=[
                "platform", "requested_device_id", "identifiers", "hostname",
                "identity_received_at",
            ])
            audit(session, "IDENTIFIED")
    if expired:
        raise EnrollmentError("EXPIRED_QR", 410)
    return session


def helper_bundle(*, session_id, browser_key, scan_token, platform, architecture=None):
    if platform not in Device.Platform.values:
        raise EnrollmentError("INVALID_PLATFORM")
    if architecture not in {None, "", "amd64", "arm64"}:
        raise EnrollmentError("INVALID_ARCHITECTURE")
    with transaction.atomic():
        session = BrowserEnrollmentSession.objects.select_for_update().filter(pk=session_id).first()
        if not session or not browser_key or session.creator_session_hash != digest(browser_key):
            raise EnrollmentError("NOT_FOUND", 404)
        if not isinstance(scan_token, str) or not secrets.compare_digest(
            session.scan_token_hash, digest(scan_token)
        ):
            raise EnrollmentError("INVALID_SCAN_TOKEN", 403)
        expired = expire_if_needed(session)
        if not expired and session.status != BrowserEnrollmentSession.Status.PENDING:
            raise EnrollmentError("ALREADY_RESOLVED", 409)
    if expired:
        raise EnrollmentError("EXPIRED_QR", 410)
    extension = ".exe" if platform == Device.Platform.WINDOWS else ""
    architectures = (architecture,) if architecture else ("amd64", "arm64")
    paths = {
        arch: Path(settings.DEVICE_REGISTRATION_HELPER_DIR) / f"{platform}-{arch}{extension}"
        for arch in architectures
    }
    if any(not path.is_file() for path in paths.values()):
        raise EnrollmentError("HELPER_NOT_BUILT", 503)
    binary_names = {
        arch: f"bioguard-register-{arch}{extension}" for arch in architectures
    }
    binary_hashes = {
        binary_names[arch]: hashlib.sha256(paths[arch].read_bytes()).hexdigest()
        for arch in architectures
    }
    binary_urls = {
        arch: f"{public_site_url()}/api/devices/browser-enrollment/session/{session.id}/binary/{platform}/{arch}/?scan_token={scan_token}"
        for arch in architectures
    }
    config = {
        "server_url": public_site_url(), "session_id": str(session.id),
        "scan_token": scan_token, "architecture": architecture or "unknown",
        "binary_sha256": binary_hashes, "binary_urls": binary_urls,
    }
    if platform == Device.Platform.WINDOWS:
        launcher_name = "run-registration.cmd"
        if architecture:
            name = binary_names[architecture]
            launcher = f'@echo off\r\ncd /d "%~dp0"\r\ncurl.exe --http1.1 --retry 3 --retry-all-errors --connect-timeout 10 -fL "{binary_urls[architecture]}" -o "{name}"\r\nif errorlevel 1 exit /b 1\r\n{name}\r\npause\r\n'
        else:
            launcher = (
                '@echo off\r\ncd /d "%~dp0"\r\n'
                f'if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (curl.exe --http1.1 --retry 3 --retry-all-errors --connect-timeout 10 -fL "{binary_urls["arm64"]}" -o "{binary_names["arm64"]}") else (curl.exe --http1.1 --retry 3 --retry-all-errors --connect-timeout 10 -fL "{binary_urls["amd64"]}" -o "{binary_names["amd64"]}")\r\n'
                'pause\r\n'
            )
    else:
        launcher_name = "run-registration.command" if platform == Device.Platform.MACOS else "run-registration.sh"
        arm_arch = "arm64" if platform == Device.Platform.MACOS else "aarch64"
        if architecture:
            name = binary_names[architecture]
            launcher = f'''#!/bin/sh
set -eu
trap 'status=$?; echo; if [ "$status" -eq 0 ]; then echo "Registration finished."; else echo "Registration failed (exit $status)."; fi; printf "Press Enter to close... "; IFS= read -r _; exit "$status"' EXIT
cd "$(dirname "$0")"
curl --http1.1 --retry 3 --retry-all-errors --connect-timeout 10 -fsSL "{binary_urls[architecture]}" -o "{name}"
chmod +x "{name}"
./"{name}"
'''
        else:
            launcher = (
                '#!/bin/sh\nset -eu\ntrap \'status=$?; echo; if [ "$status" -eq 0 ]; then echo "Registration finished."; else echo "Registration failed (exit $status)."; fi; printf "Press Enter to close... "; IFS= read -r _; exit "$status"\' EXIT\ncd "$(dirname "$0")"\n'
                f'case "$(uname -m)" in {arm_arch}) curl --http1.1 --retry 3 --retry-all-errors --connect-timeout 10 -fsSL "{binary_urls["arm64"]}" -o "{binary_names["arm64"]}"; chmod +x "{binary_names["arm64"]}"; ./"{binary_names["arm64"]}" ;; '
                f'x86_64) curl --http1.1 --retry 3 --retry-all-errors --connect-timeout 10 -fsSL "{binary_urls["amd64"]}" -o "{binary_names["amd64"]}"; chmod +x "{binary_names["amd64"]}"; ./"{binary_names["amd64"]}" ;; '
                '*) echo "Unsupported architecture"; exit 1 ;; esac\n'
            )
    output = BytesIO()
    with ZipFile(output, "w", compression=0) as archive:
        archive.writestr("scan.json", json.dumps(config))
        info = ZipInfo(launcher_name)
        info.external_attr = 0o755 << 16
        archive.writestr(info, launcher)
    return output.getvalue()


def permitted_admin(admin, organization):
    if not admin.is_authenticated or not admin.is_active or not (admin.is_admin or admin.is_superadmin):
        raise EnrollmentError("UNAUTHORIZED", 403)
    if not organization or not organization.is_active or not admin.organizations.filter(pk=organization.pk).exists():
        raise EnrollmentError("WRONG_ORGANIZATION", 403)


def expire_if_needed(session):
    if session.status == BrowserEnrollmentSession.Status.PENDING and session.expires_at <= timezone.now():
        session.status = BrowserEnrollmentSession.Status.EXPIRED
        session.resolved_at = timezone.now()
        session.save(update_fields=["status", "resolved_at"])
        audit(session, "EXPIRED", reason="EXPIRED_QR")
        return True
    return False


def creator_status(*, session_id, browser_key):
    with transaction.atomic():
        session = BrowserEnrollmentSession.objects.select_for_update().filter(pk=session_id).first()
        if not session or not browser_key or session.creator_session_hash != digest(browser_key):
            raise EnrollmentError("NOT_FOUND", 404)
        expire_if_needed(session)
        return session


def claim(*, token_hash, admin, organization, phone_key):
    permitted_admin(admin, organization)
    expired = False
    with transaction.atomic():
        session = BrowserEnrollmentSession.objects.select_for_update().filter(token_hash=token_hash).first()
        if not session:
            raise EnrollmentError("INVALID_QR", 404)
        if session.organization_id and session.organization_id != organization.id:
            raise EnrollmentError("WRONG_ORGANIZATION", 403)
        expired = expire_if_needed(session)
        if not expired:
            if not session.identity_received_at:
                raise EnrollmentError("SCAN_NOT_COMPLETE", 409)
            if session.status != BrowserEnrollmentSession.Status.PENDING or session.claimed_by_id:
                raise EnrollmentError("QR_ALREADY_USED", 409)
            session.organization = organization
            session.claimed_by = admin
            session.claimed_at = timezone.now()
            session.claimant_session_hash = digest(phone_key)
            session.save(update_fields=["organization", "claimed_by", "claimed_at", "claimant_session_hash"])
            audit(session, "CLAIMED", actor=admin)
    if expired:
        raise EnrollmentError("EXPIRED_QR", 410)
    return session


def _check_claim(session, admin, organization, phone_key):
    permitted_admin(admin, organization)
    if session.organization_id != organization.id:
        raise EnrollmentError("WRONG_ORGANIZATION", 403)
    if session.claimed_by_id != admin.id or session.claimant_session_hash != digest(phone_key):
        raise EnrollmentError("UNAUTHORIZED", 403)


def resolve(*, session_id, action, admin=None, organization=None, browser_key=None,
            phone_key=None, location=None):
    if action not in {"approve", "reject", "cancel"}:
        raise EnrollmentError("INVALID_ACTION")
    expired = False
    with transaction.atomic():
        session = BrowserEnrollmentSession.objects.select_for_update().filter(pk=session_id).first()
        if not session:
            raise EnrollmentError("NOT_FOUND", 404)
        if action == "cancel":
            if not browser_key or session.creator_session_hash != digest(browser_key):
                raise EnrollmentError("NOT_FOUND", 404)
        else:
            _check_claim(session, admin, organization, phone_key)
        expired = expire_if_needed(session)
        if not expired:
            if session.status != BrowserEnrollmentSession.Status.PENDING:
                raise EnrollmentError("ALREADY_RESOLVED", 409)
            if action == "approve":
                if not session.identity_received_at:
                    raise EnrollmentError("SCAN_NOT_COMPLETE", 409)
                if location is not None:
                    if not isinstance(location, str) or not location.strip() or len(location.strip()) > 255:
                        raise EnrollmentError("INVALID_LOCATION")
                    session.location = location.strip()
                if Device.objects.filter(
                    organization=organization, pc_id=session.requested_device_id
                ).exists():
                    raise EnrollmentError("DUPLICATE_DEVICE", 409)
                try:
                    with transaction.atomic():
                        device = Device.objects.create(
                            organization=organization,
                            pc_id=session.requested_device_id,
                            license="UNKNOWN", location=session.location,
                            platform=session.platform, identifiers=session.identifiers,
                            enrollment_status=Device.EnrollmentStatus.BROWSER_APPROVED,
                            is_active=False,
                        )
                except IntegrityError as exc:
                    raise EnrollmentError("DUPLICATE_DEVICE", 409) from exc
                session.device = device
                session.status = BrowserEnrollmentSession.Status.APPROVED
                session.approved_by = admin
            elif action == "reject":
                session.status = BrowserEnrollmentSession.Status.REJECTED
            else:
                session.status = BrowserEnrollmentSession.Status.CANCELLED
            session.resolved_at = timezone.now()
            session.save(update_fields=["status", "device", "approved_by", "resolved_at", "location"])
            audit(session, session.status.upper(), actor=admin)
    if expired:
        raise EnrollmentError("EXPIRED_QR", 410)
    return session


def cleanup_sessions():
    now = timezone.now()
    for session_id in BrowserEnrollmentSession.objects.filter(
        status=BrowserEnrollmentSession.Status.PENDING, expires_at__lte=now
    ).values_list("id", flat=True):
        with transaction.atomic():
            session = BrowserEnrollmentSession.objects.select_for_update().get(pk=session_id)
            expire_if_needed(session)
    cutoff = now - timedelta(days=1)
    BrowserEnrollmentSession.objects.filter(
        status__in=["approved", "rejected", "expired", "cancelled"], resolved_at__lte=cutoff
    ).delete()
