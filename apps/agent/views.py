"""
AD BioGuard — views.py

Faqat AgentSession modeli ishlatiladi:
  - user        (ForeignKey → Users)
  - session_id  (UUID)
  - status      ("pending" | "completed" | "expired")
  - created_at
  - expires_at

face.html, finger.html, main.py bilan to'liq mos.
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

from .models import AgentSession
from apps.common.models import BiometricFace, BiometricFingerprint, Users,Organization

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# YORDAMCHILAR
# ─────────────────────────────────────────────────────────────────

def _body(request: object) -> dict:
    try:
        return json.loads(request.body)
    except Exception:
        return {}


def _ok(data: dict, status: int = 200) -> JsonResponse:
    return JsonResponse(data, status=status)


def _err(detail: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"detail": detail}, status=status)


def _get_session(session_id: str):
    """
    session_id bo'yicha AgentSession ni qaytaradi.
    Topilmasa None, muddati tugagan bo'lsa status="expired" qilib None qaytaradi.
    """
    try:
        session = AgentSession.objects.get(session_id=session_id)
    except AgentSession.DoesNotExist:
        return None

    # expires_at o'tgan bo'lsa — expired deb belgilaymiz
    if timezone.now() > session.expires_at:
        if session.status != "expired":
            session.status = "expired"
            session.save(update_fields=["status"])
        return None  # None → caller "expired" qaytaradi

    if session.status == "expired":
        return None

    return session




def mobile_fingerprint_page(request, session_id):
    """
    GET /agent/mobile/fingerprint/<session_id>/
    → templates/bioguard/finger.html
    finger.html o'zi URL dan session_id ni oladi, template variable kerak emas.
    """
    session = _get_session(session_id)
    if session is None:
        return HttpResponse(
            "<h2 style='font-family:monospace;text-align:center;margin-top:40vh;color:#ff3355'>"
            "Sessiya muddati tugadi. QR kodni qayta skanerlang.</h2>",
            status=410,
        )
    return render(request, "finger.html")


def mobile_face_page(request, session_id):
    """
    GET /agent/mobile/face/<session_id>/
    → templates/bioguard/face.html
    """
    session = _get_session(session_id)
    if session is None:
        return HttpResponse(
            "<h2 style='font-family:monospace;text-align:center;margin-top:40vh;color:#ff3355'>"
            "Sessiya muddati tugadi. QR kodni qayta skanerlang.</h2>",
            status=410,
        )
    return render(request, "face.html")




@csrf_exempt
@require_http_methods(["POST"])
def agent_session_start(request):
    """
    POST /api/agent/session/start/
    Body : { "username": "john" }
    Return: { "session_id": "<uuid>" }
    """
    data     = _body(request)
    username = data.get("username", "").strip()

    if not username:
        return _err("username required")

    org=Organization.objects.get(slug='no_organization')
    # Users modelidan foydalanuvchini topamiz
    try:
        user = Users.objects.get(username=username)
    except Users.DoesNotExist:
        return _err("Foydalanuvchi topilmadi", status=404)

    # Foydalanuvchining eski pending sessiyalarini tozalaymiz
    AgentSession.objects.filter(
        user=user,
        status="pending",
    ).update(status="expired")

    # Yangi sessiya — expires_at modeldagi save() da avtomatik o'rnatiladi
    session = AgentSession.objects.create(user=user)

    logger.info("[session_start] user=%s  id=%s", username, session.session_id)

    return _ok({
        "session_id": str(session.session_id),
        "username":   username,
        "status":     session.status,
    })



@csrf_exempt
@require_http_methods(["POST"])
def face_agent_check(request):
    """
    POST /api/face/agent/check/
    Body : { "session_id": "...", "username": "...", "image": "<base64>" }
    Return: { "status": "verified" }
         yoki { "status": "failed", "detail": "Yuz tanilmadi" }
    """
    data       = _body(request)
    session_id = data.get("session_id", "").strip()
    username   = data.get("username",   "").strip()
    image_b64  = data.get("image",      "").strip()

    if not session_id or not username or not image_b64:
        return _err("session_id, username, image required")

    session = _get_session(session_id)
    if session is None:
        return _err("Sessiya topilmadi yoki muddati tugadi", status=410)

    # ── 1. Userning face embeddinglarini olish ────────────────────
    face_records = BiometricFace.objects.filter(user=session.user)
    if not face_records.exists():
        return _ok({"status": "failed", "detail": "Bazada yuz yo'q"})

    # ── 2. Base64 decode ──────────────────────────────────────────
    try:
        img_bytes = base64.b64decode(image_b64)
    except Exception as e:
        return _err(f"Base64 decode xato: {e}")

    # ── 3. Incoming embedding olish ───────────────────────────────
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        incoming_bytes = extract_embedding(tmp_path)

    except Exception as e:
        return _ok({"status": "failed", "detail": f"Yuz topilmadi: {e}"})

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    incoming_embedding = np.frombuffer(incoming_bytes, dtype=np.float64)

    # ── 4. Eng yaxshi similarity topish ──────────────────────────
    best_similarity = 0.0

    for face in face_records:
        saved_bytes = face.get_embedding()
        if not saved_bytes:
            continue

        saved_embedding = np.frombuffer(saved_bytes, dtype=np.float64)
        similarity = _cosine_similarity(saved_embedding, incoming_embedding)

        if similarity > best_similarity:
            best_similarity = similarity

    logger.info("[face_agent_check] similarity=%.4f user=%s id=%s",
                best_similarity, username, session_id)

    # ── 5. Threshold tekshirish ───────────────────────────────────
    THRESHOLD = 0.65
    print(best_similarity)

    if best_similarity < THRESHOLD:
        logger.warning("[face_agent_check] FAILED user=%s id=%s", username, session_id)
        return _ok({
            "status": "failed",
            "detail": "Yuz tanilmadi. Qayta urining.",
            "similarity": round(float(best_similarity), 4)
        })

    # ── 6. Yangi embedding saqlash (0.65–0.80 oraliq, limit < 10) ─
    if 0.70 <= best_similarity <= 0.80:
        if BiometricFace.objects.filter(user=session.user).count() < 10:
            new_face = BiometricFace(user=session.user)
            new_face.set_embedding(incoming_bytes)
            new_face.save()

    # ── 7. Session yakunlash ──────────────────────────────────────
    session.status = "completed"
    session.save(update_fields=["status"])

    logger.info("[face_agent_check] VERIFIED user=%s id=%s", username, session_id)
    return _ok({
        "status": "verified",
        "similarity": round(float(best_similarity), 4)
    })


@csrf_exempt
@require_http_methods(["POST"])
def face_phone_submit(request, session_id):
    """
    POST /api/face/phone/submit/<session_id>/
    Body : { "session_id": "...", "image": "<base64>", "source": "mobile_web" }
    Return: { "status": "completed" }  → face.html onSuccess()
         yoki { "status": "failed", "detail": "..." } → face.html onError()
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

    # ── 1. Face records ───────────────────────────────────────────
    face_records = BiometricFace.objects.filter(user=session.user)
    if not face_records.exists():
        return _ok({"status": "failed", "detail": "Bazada yuz yo'q"})

    # ── 2. Base64 decode ──────────────────────────────────────────
    try:
        img_bytes = base64.b64decode(image_b64)
    except Exception as e:
        return _err(f"Base64 decode xato: {e}")

    # ── 3. Incoming embedding ─────────────────────────────────────
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        incoming_bytes = extract_embedding(tmp_path)

    except Exception as e:
        logger.warning("[face_phone_submit] embedding xato: %s  id=%s", e, session_id)
        return _ok({"status": "failed", "detail": f"Yuz topilmadi: {e}"})

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    incoming_embedding = np.frombuffer(incoming_bytes, dtype=np.float64)

    # ── 4. Similarity hisoblash ───────────────────────────────────
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

    print(best_similarity)

    if best_similarity < THRESHOLD:
        logger.warning("[face_phone_submit] FAILED similarity=%.4f  id=%s", best_similarity, session_id)
        return _ok({
            "status":     "failed",
            "detail":     "Yuz tanilmadi. Qayta urining.",
            "similarity": round(float(best_similarity), 4)
        })

    # ── 5. Yangi embedding saqlash (0.70–0.80 oraliq, limit < 10) ─
    if 0.70 <= best_similarity <= 0.80:
        if BiometricFace.objects.filter(user=session.user).count() < 10:
            new_face = BiometricFace(user=session.user)
            new_face.set_embedding(incoming_bytes)
            new_face.save()

    # ── 6. Session yakunlash ──────────────────────────────────────
    session.status = "completed"
    session.save(update_fields=["status"])

    logger.info("[face_phone_submit] COMPLETED  id=%s", session_id)
    return _ok({
        "status":     "completed",
        "similarity": round(float(best_similarity), 4)
    })




@require_http_methods(["GET"])
def agent_face_phone_status(request, session_id):
    """
    GET /api/agent/face/phone/status/<session_id>/
    Return: plain text  "completed" | "expired" | "pending"
    """
    session = _get_session(session_id)

    if session is None:
        return HttpResponse("expired", content_type="text/plain")

    if session.status == "completed":
        return HttpResponse("completed", content_type="text/plain")

    return HttpResponse("pending", content_type="text/plain")


@csrf_exempt
def fingerprint_phone_submit(request, session_id):
    session = _get_session(session_id)

    if session is None:
        return _err("Sessiya topilmadi yoki muddati tugadi", status=410)

    if request.method == "GET":
        fingerprint = BiometricFingerprint.objects.filter(user=session.user).first()

        if not fingerprint:
            return _err("Fingerprint topilmadi")

        saved = fingerprint.get_embedding()

        if not saved:
            return _err("Credential yo'q")

        try:
            saved_raw, saved_client, saved_attestation = saved.decode().split("|")
        except:
            return _err("Credential buzilgan")

        challenge = secrets.token_urlsafe(32)

        

        return _ok({
            "challenge": challenge,
            "credential_id": saved_raw
        })

    elif request.method == "POST":
        data = _body(request)

        raw_id = data.get("rawId")

        def normalize_base64(v):
            if not v:
                return ""
            return v.replace("-", "+").replace("_", "/").rstrip("=")

        raw_id_norm = normalize_base64(raw_id)

        fingerprint_records = BiometricFingerprint.objects.filter(user=session.user)

        matched = False

        for fp in fingerprint_records:
            saved = fp.get_embedding()

            if not saved:
                continue

            try:
                saved_raw, saved_client, saved_attestation = saved.decode().split("|")
            except:
                continue

            if normalize_base64(saved_raw) == raw_id_norm:
                matched = True
                break

        if matched:
            session.status = "completed"
            session.save(update_fields=["status"])

            return _ok({
                "status": "completed"
            })

        return _ok({
            "status": "failed"
        })

@require_http_methods(["GET"])
def agent_fingerprint_phone_status(request, session_id):
    """
    GET /api/agent/fingerprint/phone/status/<session_id>/
    Return: plain text  "completed" | "expired" | "pending"
    """
    session = _get_session(session_id)

    if session is None:
        return HttpResponse("expired", content_type="text/plain")

    if session.status == "completed":
        return HttpResponse("completed", content_type="text/plain")

    return HttpResponse("pending", content_type="text/plain")