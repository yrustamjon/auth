"""JSON views for the separate frontend; enrollment policy stays in the service."""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from .browser_views import _browser_key, _error, _payload, _selected_org
from .browser_enrollment import EnrollmentError, claim, digest, expire_if_needed
from .models import BrowserEnrollmentSession

def _approval(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error':'LOGIN_REQUIRED'},status=401)
    token_hash=request.session.get('browser_enrollment_token_hash')
    if not token_hash:
        return JsonResponse({'error':'NOT_FOUND'},status=404)
    try:
        organization=_selected_org(request)
        claimed_id=request.session.get('browser_enrollment_claimed_id')
        if claimed_id:
            enrollment=BrowserEnrollmentSession.objects.filter(pk=claimed_id).first()
            if not enrollment:
                raise EnrollmentError('NOT_FOUND',404)
            if enrollment.organization_id != organization.id:
                raise EnrollmentError('WRONG_ORGANIZATION',403)
            if enrollment.claimed_by_id != request.user.id or enrollment.claimant_session_hash != digest(_browser_key(request)):
                raise EnrollmentError('UNAUTHORIZED',403)
            expire_if_needed(enrollment)
        else:
            enrollment=claim(token_hash=token_hash,admin=request.user,organization=organization,phone_key=_browser_key(request))
            request.session['browser_enrollment_claimed_id']=str(enrollment.id)
            request.session.save()
        return JsonResponse({'enrollment':_payload(enrollment),'organization':{'id':organization.id,'name':organization.name}})
    except EnrollmentError as error:
        return _error(error)

@csrf_protect
@require_POST
def claim_json(request):
    try:
        data=json.loads(request.body)
        token=data.get('token')
        if not isinstance(token,str) or not 20 <= len(token) <= 128:
            raise ValueError
    except (ValueError,AttributeError):
        return JsonResponse({'error':'INVALID_REQUEST'},status=400)
    token_hash=digest(token)
    if not BrowserEnrollmentSession.objects.filter(token_hash=token_hash).exists():
        return JsonResponse({'error':'NOT_FOUND'},status=404)
    if request.session.get('browser_enrollment_token_hash') != token_hash:
        request.session.pop('browser_enrollment_claimed_id',None)
    request.session['browser_enrollment_token_hash']=token_hash
    request.session.save()
    return _approval(request)

@ensure_csrf_cookie
@require_GET
def approval_json(request):
    return _approval(request)

