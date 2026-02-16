# common/middleware.py
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
from django.http import JsonResponse

class SessionHijackProtectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            session = request.session

            ip = self.get_ip(request)
            ua = request.META.get("HTTP_USER_AGENT", "")

            # birinchi marta saqlaymiz
            if "ip" not in session:
                session["ip"] = ip
                session["ua"] = ua

            else:
                # agar boshqa joydan kelsa → CHIQAR
                if session.get("ip") != ip or session.get("ua") != ua:
                    logout(request)
                    session.flush()

                    return JsonResponse(
                        {
                            "detail": "Session hijacking detected. Logged out."
                        },
                        status=403
                    )

        return self.get_response(request)

    def get_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0]
        return request.META.get("REMOTE_ADDR")
