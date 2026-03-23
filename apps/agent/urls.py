"""
AD BioGuard — urls.py

Barcha URL lar quyidagi fayllar bilan to'liq mos:
  face.html    → POST /api/face/phone/submit/<session_id>/
  finger.html  → POST /api/fingerprint/phone/submit/<session_id>/
  main.py      → POST /api/agent/session/start/
                 POST /api/face/agent/check/
                 GET  /api/agent/face/phone/status/<session_id>/
                 GET  /api/agent/fingerprint/phone/status/<session_id>/
                 GET  /agent/mobile/fingerprint/<session_id>/   (QR sahifasi)
                 GET  /agent/mobile/face/<session_id>/          (QR sahifasi)
"""

from django.urls import path
from . import views

urlpatterns = [

    # ── QR skanerlanganda telefonda ochiladi ───────────────────────
    path(
        "agent/mobile/fingerprint/<str:session_id>/",
        views.mobile_fingerprint_page,
        name="mobile_fingerprint",
    ),
    path(
        "agent/mobile/face/<str:session_id>/",
        views.mobile_face_page,
        name="mobile_face",
    ),

    # ── Session ────────────────────────────────────────────────────
    path(
        "api/agent/session/start/",
        views.agent_session_start,
        name="agent_session_start",
    ),

    # ── Face ───────────────────────────────────────────────────────
    path(
        "api/face/agent/check/",
        views.face_agent_check,
        name="face_agent_check",
    ),
    path(
        "api/face/phone/submit/<str:session_id>/",
        views.face_phone_submit,
        name="face_phone_submit",
    ),
    path(
        "api/agent/face/phone/status/<str:session_id>/",
        views.agent_face_phone_status,
        name="agent_face_phone_status",
    ),

    # ── Fingerprint ────────────────────────────────────────────────
    path(
        "api/agent/fingerprint/phone/submit/<str:session_id>/",
        views.fingerprint_phone_submit,
        name="fingerprint_phone_submit",
    ),
    path(
        "api/agent/fingerprint/phone/status/<str:session_id>/",
        views.agent_fingerprint_phone_status,
        name="agent_fingerprint_phone_status",
    ),
]