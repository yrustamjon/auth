"""
AD BioGuard — views.py
"""

import base64
import json
import logging
import os
import tempfile
import secrets

from django.http                  import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts             import render, get_object_or_404
from django.utils                 import timezone

import numpy as np

from apps.biometrik.embedding import extract_embedding
from apps.biometrik.views import _cosine_similarity
from apps.org.models import OrgToken

from .models import AgentSession
from apps.common.models import (
    BiometricFace, BiometricFingerprint,
    Device, Users, Organization,
    AccessLogs,                          # ← LOG import
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# YORDAMCHILAR
# ─────────────────────────────────────────────────────────────────

def _body(request):
    try:
        return json.loads(request.body)
    except Exception:
        return {}

def _ok(data, status=200):
    return JsonResponse(data, status=status)

def _err(detail, status=400):
    return JsonResponse({"detail": detail}, status=status)

def _get_session(session_id):
    try:
        session = AgentSession.objects.get(session_id=session_id)
    except AgentSession.DoesNotExist:
        return None

    if timezone.now() > session.expires_at:
        if session.status != "expired":
            session.status = "expired"
            session.save(update_fields=["status"])
        return None

    if session.status == "expired":
        return None

    return session


def _write_log(session, device, success, cause=""):
    """
    AccessLogs jadvaliga yozuvchi yordamchi funksiya.
    session.user, device, organization avtomatik olinadi.
    """
    try:
        AccessLogs.objects.create(
            organization=device.organization,
            user=session.user,
            device=device,
            success=success,
            cause=cause,
        )
    except Exception as e:
        logger.error("[access_log] yozishda xato: %s", e)


# ─────────────────────────────────────────────────────────────────
# SAHIFALAR
# ─────────────────────────────────────────────────────────────────

def mobile_fingerprint_page(request, session_id):
    session = _get_session(session_id)
    if session is None:
        return HttpResponse(
            "<h2 style='font-family:monospace;text-align:center;margin-top:40vh;color:#ff3355'>"
            "Sessiya muddati tugadi. QR kodni qayta skanerlang.</h2>",
            status=410,
        )
    return render(request, "finger.html")


def mobile_face_page(request, session_id):
    session = _get_session(session_id)
    if session is None:
        return HttpResponse(
            "<h2 style='font-family:monospace;text-align:center;margin-top:40vh;color:#ff3355'>"
            "Sessiya muddati tugadi. QR kodni qayta skanerlang.</h2>",
            status=410,
        )
    return render(request, "face.html")


# ─────────────────────────────────────────────────────────────────
# SESSION START
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def agent_session_start(request):
    data     = _body(request)
    username = data.get("username", "").strip()
    pc_id    = data.get("pc_id", "").strip()

    if not username:
        return _err("username required")

    device = Device.objects.get(pc_id=pc_id)
    org    = device.organization

    try:
        user = Users.objects.get(username=username, organization=org)
    except Users.DoesNotExist:
        return _err("Foydalanuvchi topilmadi", status=404)

    if not all([user.status, device.is_active, org.is_active]):
        return _err("username required")

    AgentSession.objects.filter(user=user, status="pending").update(status="expired")

    session = AgentSession.objects.create(user=user)
    # device ni session ga biriktiramiz — log uchun kerak bo'ladi
    session._device = device          # ← vaqtinchalik atribut (DB saqlashsiz)

    logger.info("[session_start] user=%s  id=%s", username, session.session_id)

    return _ok({
        "session_id": str(session.session_id),
        "username":   username,
        "status":     session.status,
    })


# ─────────────────────────────────────────────────────────────────
# YUZ — AGENT (desktop polling)
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def face_agent_check(request):
    """
    POST /api/face/agent/check/
    Body: { "session_id", "username", "image": "<base64>", "pc_id" }
    """
    data       = _body(request)
    session_id = data.get("session_id", "").strip()
    username   = data.get("username",   "").strip()
    image_b64  = data.get("image",      "").strip()
    pc_id      = data.get("pc_id",      "").strip()          # ← LOG uchun

    if not session_id or not username or not image_b64:
        return _err("session_id, username, image required")

    session = _get_session(session_id)
    if session is None:
        return _err("Sessiya topilmadi yoki muddati tugadi", status=410)

    # Device — log uchun kerak
    try:
        device = Device.objects.get(pc_id=pc_id) if pc_id else session.user.device_set.first()
    except Device.DoesNotExist:
        device = None

    # ── 1. Face records ───────────────────────────────────────────
    face_records = BiometricFace.objects.filter(user=session.user)
    if not face_records.exists():
        if device:
            _write_log(session, device, success=False, cause="Bazada yuz yo'q")   # ← LOG
        return _ok({"status": "failed", "detail": "Bazada yuz yo'q"})

    # ── 2. Base64 decode ──────────────────────────────────────────
    try:
        img_bytes = base64.b64decode(image_b64)
    except Exception as e:
        return _err(f"Base64 decode xato: {e}")

    # ── 3. Embedding ──────────────────────────────────────────────
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name
        incoming_bytes = extract_embedding(tmp_path)
    except Exception as e:
        if device:
            _write_log(session, device, success=False, cause=f"Yuz topilmadi: {e}")  # ← LOG
        return _ok({"status": "failed", "detail": f"Yuz topilmadi: {e}"})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    incoming_embedding = np.frombuffer(incoming_bytes, dtype=np.float64)

    # ── 4. Similarity ─────────────────────────────────────────────
    best_similarity = 0.0
    for face in face_records:
        saved_bytes = face.get_embedding()
        if not saved_bytes:
            continue
        saved_embedding = np.frombuffer(saved_bytes, dtype=np.float64)
        sim = _cosine_similarity(saved_embedding, incoming_embedding)
        if sim > best_similarity:
            best_similarity = sim

    logger.info("[face_agent_check] similarity=%.4f user=%s id=%s",
                best_similarity, username, session_id)

    THRESHOLD = 0.65

    # ── 5. Threshold ──────────────────────────────────────────────
    if best_similarity < THRESHOLD:
        logger.warning("[face_agent_check] FAILED user=%s id=%s", username, session_id)
        if device:
            _write_log(                                                            # ← LOG
                session, device,
                success=False,
                cause=f"Yuz tanilmadi (similarity={best_similarity:.4f})",
            )
        return _ok({
            "status":     "failed",
            "detail":     "Yuz tanilmadi. Qayta urining.",
            "similarity": round(float(best_similarity), 4),
        })

    # ── 6. Adaptive embedding saqlash ────────────────────────────
    if 0.70 <= best_similarity <= 0.80:
        if BiometricFace.objects.filter(user=session.user).count() < 10:
            new_face = BiometricFace(user=session.user)
            new_face.set_embedding(incoming_bytes)
            new_face.save()

    # ── 7. Session & LOG ──────────────────────────────────────────
    session.status = "completed"
    session.save(update_fields=["status"])

    if device:
        _write_log(session, device, success=True, cause="Yuz tasdiqlandi")        # ← LOG

    logger.info("[face_agent_check] VERIFIED user=%s id=%s", username, session_id)
    return _ok({
        "status":     "verified",
        "similarity": round(float(best_similarity), 4),
    })


# ─────────────────────────────────────────────────────────────────
# YUZ — TELEFON (mobile web submit)
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def face_phone_submit(request, session_id):
    """
    POST /api/face/phone/submit/<session_id>/
    Body: { "image": "<base64>", "source": "mobile_web" }
    """
    data      = _body(request)
    image_b64 = data.get("image", "").strip()

    if not image_b64:
        return _err("image required")

    session = _get_session(session_id)
    if session is None:
        return _err("Sessiya topilmadi yoki muddati tugadi", status=410)

    if session.status == "completed":
        return _ok({"status": "completed"})

    # Device — session.user ga biriktirilgan birinchi device
    device = Device.objects.filter(organization=session.user.organization).first()

    face_records = BiometricFace.objects.filter(user=session.user)
    if not face_records.exists():
        if device:
            _write_log(session, device, success=False, cause="Bazada yuz yo'q")   # ← LOG
        return _ok({"status": "failed", "detail": "Bazada yuz yo'q"})

    try:
        img_bytes = base64.b64decode(image_b64)
    except Exception as e:
        return _err(f"Base64 decode xato: {e}")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name
        incoming_bytes = extract_embedding(tmp_path)
    except Exception as e:
        logger.warning("[face_phone_submit] embedding xato: %s  id=%s", e, session_id)
        if device:
            _write_log(session, device, success=False, cause=f"Yuz topilmadi: {e}")  # ← LOG
        return _ok({"status": "failed", "detail": f"Yuz topilmadi: {e}"})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    incoming_embedding = np.frombuffer(incoming_bytes, dtype=np.float64)

    best_similarity = 0.0
    for face in face_records:
        saved_bytes = face.get_embedding()
        if not saved_bytes:
            continue
        saved_embedding = np.frombuffer(saved_bytes, dtype=np.float64)
        sim = _cosine_similarity(saved_embedding, incoming_embedding)
        if sim > best_similarity:
            best_similarity = sim

    logger.info("[face_phone_submit] similarity=%.4f  id=%s", best_similarity, session_id)

    THRESHOLD = 0.65

    if best_similarity < THRESHOLD:
        logger.warning("[face_phone_submit] FAILED similarity=%.4f  id=%s", best_similarity, session_id)
        if device:
            _write_log(                                                            # ← LOG
                session, device,
                success=False,
                cause=f"Yuz tanilmadi (similarity={best_similarity:.4f})",
            )
        return _ok({
            "status":     "failed",
            "detail":     "Yuz tanilmadi. Qayta urining.",
            "similarity": round(float(best_similarity), 4),
        })

    if 0.70 <= best_similarity <= 0.80:
        if BiometricFace.objects.filter(user=session.user).count() < 10:
            new_face = BiometricFace(user=session.user)
            new_face.set_embedding(incoming_bytes)
            new_face.save()

    session.status = "completed"
    session.save(update_fields=["status"])

    if device:
        _write_log(session, device, success=True, cause="Yuz tasdiqlandi (telefon)")  # ← LOG

    logger.info("[face_phone_submit] COMPLETED  id=%s", session_id)
    return _ok({
        "status":     "completed",
        "similarity": round(float(best_similarity), 4),
    })


# ─────────────────────────────────────────────────────────────────
# YUZ — STATUS (agent polling)
# ─────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def agent_face_phone_status(request, session_id):
    session = _get_session(session_id)
    if session is None:
        return HttpResponse("expired", content_type="text/plain")
    if session.status == "completed":
        return HttpResponse("completed", content_type="text/plain")
    return HttpResponse("pending", content_type="text/plain")


# ─────────────────────────────────────────────────────────────────
# BARMOQ IZI — TELEFON
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
def fingerprint_phone_submit(request, session_id):
    session = _get_session(session_id)
    if session is None:
        return _err("Sessiya topilmadi yoki muddati tugadi", status=410)

    device = Device.objects.filter(organization=session.user.organization).first()

    if request.method == "GET":
        fingerprint = BiometricFingerprint.objects.filter(user=session.user).first()
        if not fingerprint:
            return _err("Fingerprint topilmadi")

        saved = fingerprint.get_embedding()
        if not saved:
            return _err("Credential yo'q")

        try:
            saved_raw, saved_client, saved_attestation = saved.decode().split("|")
        except Exception:
            return _err("Credential buzilgan")

        challenge = secrets.token_urlsafe(32)
        return _ok({"challenge": challenge, "credential_id": saved_raw})

    elif request.method == "POST":
        data   = _body(request)
        raw_id = data.get("rawId")

        def normalize_base64(v):
            if not v:
                return ""
            return v.replace("-", "+").replace("_", "/").rstrip("=")

        raw_id_norm         = normalize_base64(raw_id)
        fingerprint_records = BiometricFingerprint.objects.filter(user=session.user)
        matched             = False

        for fp in fingerprint_records:
            saved = fp.get_embedding()
            if not saved:
                continue
            try:
                saved_raw, _, _ = saved.decode().split("|")
            except Exception:
                continue
            if normalize_base64(saved_raw) == raw_id_norm:
                matched = True
                break

        if matched:
            session.status = "completed"
            session.save(update_fields=["status"])

            if device:
                _write_log(session, device, success=True, cause="Barmoq izi tasdiqlandi")  # ← LOG

            return _ok({"status": "completed"})

        # ── muvaffaqiyatsiz ───────────────────────────────────────
        if device:
            _write_log(session, device, success=False, cause="Barmoq izi tanilmadi")       # ← LOG

        return _ok({"status": "failed"})


# ─────────────────────────────────────────────────────────────────
# BARMOQ IZI — STATUS
# ─────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def agent_fingerprint_phone_status(request, session_id):
    session = _get_session(session_id)
    if session is None:
        return HttpResponse("expired", content_type="text/plain")
    if session.status == "completed":
        return HttpResponse("completed", content_type="text/plain")
    return HttpResponse("pending", content_type="text/plain")


# ─────────────────────────────────────────────────────────────────
# BOSHQALAR
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def ValidetAgent(request):
    data = json.loads(request.body)
    try:
        device = Device.objects.get(
            pc_id=data["device_uuid"],
            license=data["windows_license"],
        )
    except Device.DoesNotExist:
        return JsonResponse({"ok": False, "detail": "Device topilmadi"}, status=404)

    if not device.is_active:
        return JsonResponse({"ok": False, "detail": "Device faol emas"}, status=403)

    try:
        OrgToken.objects.get(org=device.organization)
    except OrgToken.DoesNotExist:
        return JsonResponse({"ok": False, "detail": "Token topilmadi"}, status=404)

    return JsonResponse({"ok": True})


def health(request):
    return JsonResponse({"ok": True})


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class DeviceStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        pc_id    = request.GET.get("pc_id")
        username = request.GET.get("username")
        return Response({"pc_id": pc_id, "username": username, "status": "ok"})