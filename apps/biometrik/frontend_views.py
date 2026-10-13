from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from .models import FingerprintSession
from .webauthn_service import b64, rp

@require_GET
def fingerprint_options(request,session_id):
    session=FingerprintSession.objects.select_related('user__organization').filter(session_id=session_id,status='pending',expires_at__gt=timezone.now()).first()
    if not session or not session.challenge or not session.user.status or not session.user.organization.is_active:
        return JsonResponse({'detail':'Registration session expired'},status=410)
    rp_id,origin=rp()
    return JsonResponse({'challenge':b64(bytes(session.challenge)),'rp_id':rp_id,'origin':origin,'user_id':b64(str(session.user_id).encode()),'username':session.user.username})

