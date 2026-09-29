import json
import secrets
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from apps.common.models import Organization
from .browser_enrollment import (
    EnrollmentError, claim, create_session, creator_status, digest, display_code_for, permitted_admin,
    helper_bundle, resolve, submit_identity, expire_if_needed,
)
from .models import BrowserEnrollmentSession


def _browser_key(request):
    if request.session.session_key is None:
        request.session.create()
    return request.session.session_key


def _error(error):
    return JsonResponse({"error": error.code}, status=error.status)


def _payload(session):
    data = {
        "session_id": str(session.id), "status": session.status,
        "platform": session.platform, "device_id": session.requested_device_id,
        "identifiers": session.identifiers, "location": session.location,
        "hostname": session.hostname, "identity_ready": bool(session.identity_received_at),
        "display_code": display_code_for(session), "expires_at": session.expires_at.isoformat(),
    }
    if session.device:
        data["enrollment_status"] = session.device.enrollment_status
    return data


def _selected_org(request):
    org = Organization.objects.filter(
        pk=request.session.get("current_org_id"), is_active=True
    ).first()
    permitted_admin(request.user, org)
    return org


@ensure_csrf_cookie
@require_GET
def scan_page(request):
    _browser_key(request)
    return render(request, "device_scan.html")


@csrf_protect
@require_POST
def session_create(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict) or data:
            return JsonResponse({"error": "UNEXPECTED_FIELDS"}, status=400)
        session, url, svg, scan_token = create_session(
            browser_key=_browser_key(request), source_ip=request.META.get("REMOTE_ADDR"),
        )
    except (ValueError, TypeError):
        return JsonResponse({"error": "INVALID_REQUEST"}, status=400)
    except EnrollmentError as error:
        return _error(error)
    result = _payload(session)
    result.update({"qr_url": url, "qr_svg": svg, "scan_token": scan_token})
    return JsonResponse(result, status=201)


@csrf_exempt
@require_POST
def session_identity(request, session_id):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError
        session = submit_identity(
            session_id=session_id, scan_token=data.get("scan_token"),
            platform=data.get("platform"), device_id=data.get("device_id"),
            identifiers=data.get("identifiers"), hostname=data.get("hostname", ""),
        )
    except (ValueError, TypeError):
        return JsonResponse({"error": "INVALID_REQUEST"}, status=400)
    except EnrollmentError as error:
        return _error(error)
    return JsonResponse(_payload(session))


@csrf_protect
@require_POST
def session_helper(request, session_id, platform):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError
        bundle = helper_bundle(
            session_id=session_id, browser_key=_browser_key(request),
            scan_token=data.get("scan_token"), platform=platform,
            architecture=data.get("architecture"),
        )
    except (ValueError, TypeError):
        return JsonResponse({"error": "INVALID_REQUEST"}, status=400)
    except EnrollmentError as error:
        return _error(error)
    response = HttpResponse(bundle, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="bioguard-registration-{platform}.zip"'
    response["Cache-Control"] = "no-store"
    return response


@csrf_exempt
@require_GET
def session_binary(request, session_id, platform, architecture):
    if platform not in {"windows", "macos", "linux"} or architecture not in {"amd64", "arm64"}:
        return JsonResponse({"error": "INVALID_BINARY"}, status=400)
    token = request.GET.get("scan_token")
    if not token:
        return JsonResponse({"error": "INVALID_SCAN_TOKEN"}, status=403)
    session = BrowserEnrollmentSession.objects.filter(pk=session_id).first()
    if not session:
        return JsonResponse({"error": "NOT_FOUND"}, status=404)
    if expire_if_needed(session) or session.status != BrowserEnrollmentSession.Status.PENDING:
        return JsonResponse({"error": "EXPIRED_QR"}, status=410)
    if not secrets.compare_digest(session.scan_token_hash, digest(token)):
        return JsonResponse({"error": "INVALID_SCAN_TOKEN"}, status=403)
    suffix = ".exe" if platform == "windows" else ""
    path = Path(settings.DEVICE_REGISTRATION_HELPER_DIR) / f"{platform}-{architecture}{suffix}"
    if not path.is_file():
        return JsonResponse({"error": "HELPER_NOT_BUILT"}, status=503)
    response = FileResponse(path.open("rb"), content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{path.name}"'
    response["Cache-Control"] = "private, no-store"
    return response


@require_GET
def session_status(request, session_id):
    try:
        session = creator_status(session_id=session_id, browser_key=_browser_key(request))
    except EnrollmentError as error:
        return _error(error)
    return JsonResponse(_payload(session))


@csrf_protect
@require_POST
def session_cancel(request, session_id):
    try:
        session = resolve(session_id=session_id, action="cancel", browser_key=_browser_key(request))
    except EnrollmentError as error:
        return _error(error)
    return JsonResponse(_payload(session))


@require_GET
def qr_entry(request, token):
    token_hash = digest(token)
    if not BrowserEnrollmentSession.objects.filter(token_hash=token_hash).exists():
        return render(request, "device_enroll_approval.html", {"error": "QR token topilmadi."}, status=404)
    request.session["browser_enrollment_token_hash"] = token_hash
    request.session.pop("browser_enrollment_claimed_id", None)
    request.session.save()
    if request.user.is_authenticated:
        return redirect("device_enroll_approval")
    return redirect(f"{settings.LOGIN_URL}?{urlencode({'next': '/device-enroll/approval/'})}")


@ensure_csrf_cookie
@login_required
@require_GET
def approval_page(request):
    token_hash = request.session.get("browser_enrollment_token_hash")
    if not token_hash:
        return render(request, "device_enroll_approval.html", {"error": "QR sessiya topilmadi."}, status=400)
    try:
        organization = _selected_org(request)
        claimed_id = request.session.get("browser_enrollment_claimed_id")
        if claimed_id:
            session = BrowserEnrollmentSession.objects.filter(pk=claimed_id).first()
            if not session:
                raise EnrollmentError("NOT_FOUND", 404)
            if session.organization_id != organization.id:
                raise EnrollmentError("WRONG_ORGANIZATION", 403)
            if session.claimed_by_id != request.user.id or session.claimant_session_hash != digest(_browser_key(request)):
                raise EnrollmentError("UNAUTHORIZED", 403)
        else:
            session = claim(
                token_hash=token_hash, admin=request.user,
                organization=organization, phone_key=_browser_key(request),
            )
            request.session["browser_enrollment_claimed_id"] = str(session.id)
            request.session.save()
    except EnrollmentError as error:
        return render(request, "device_enroll_approval.html", {"error": error.code}, status=error.status)
    return render(request, "device_enroll_approval.html", {
        "enrollment": _payload(session), "organization": organization,
    })


@csrf_protect
@login_required
@require_POST
def session_approve(request, session_id):
    data = {}
    if request.content_type == "application/json" and request.body:
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({"error": "INVALID_REQUEST"}, status=400)
    try:
        session = resolve(
            session_id=session_id, action="approve", admin=request.user,
            organization=_selected_org(request), phone_key=_browser_key(request),
            location=data.get("location"),
        )
    except EnrollmentError as error:
        return _error(error)
    return JsonResponse(_payload(session))


@csrf_protect
@login_required
@require_POST
def session_reject(request, session_id):
    try:
        session = resolve(
            session_id=session_id, action="reject", admin=request.user,
            organization=_selected_org(request), phone_key=_browser_key(request),
        )
    except EnrollmentError as error:
        return _error(error)
    return JsonResponse(_payload(session))


@ensure_csrf_cookie
@login_required
@require_GET
def admin_scanner_page(request):
    try:
        organization = _selected_org(request)
    except EnrollmentError as error:
        return render(request, "device_qr_scanner.html", {"error": error.code}, status=error.status)
    public_url = urlsplit(settings.PUBLIC_SITE_URL)
    public_origin = f"{public_url.scheme}://{public_url.netloc}"
    return render(request, "device_qr_scanner.html", {
        "organization": organization,
        "public_site_origin": public_origin,
    })
