"""Public signup keeps the existing mandatory organization relationships."""
import json
import uuid
from django.contrib.auth import login
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from .models import AdminUser, Organization, Users, Roles
from apps.device.browser_views import _browser_key
from apps.device.browser_enrollment import creator_status, claim, resolve, EnrollmentError

def workspace_data(org):
    return {'id':org.id,'name':org.name,'kind':org.kind,'status':org.approval_status,
        'active':org.is_active,'note':org.review_note}

@csrf_protect
@require_POST
def register(request):
    if request.user.is_authenticated:
        return JsonResponse({'detail':'Avval joriy hisobdan chiqing.'},status=409)
    try:
        data=json.loads(request.body)
        if not isinstance(data,dict): raise ValueError
        kind=data.get('kind');username=data.get('username');password=data.get('password')
        fio=data.get('fio');company_name=data.get('company_name')
        if kind not in Organization.Kind.values or not isinstance(username,str) or not isinstance(password,str): raise ValueError
        username=username.strip()
        if not username or len(username)>150 or len(password)>128: raise ValueError
        UnicodeUsernameValidator()(username)
        if not isinstance(fio,str) or not fio.strip() or len(fio.strip())>255: raise ValueError
        if kind=='company' and (not isinstance(company_name,str) or not company_name.strip() or len(company_name.strip())>255): raise ValueError
        owner=AdminUser(username=username,is_staff=False,is_superadmin=False,is_admin=True)
        validate_password(password,owner)
        if AdminUser.objects.filter(username=username).exists():
            return JsonResponse({'detail':'Bu login band.'},status=400)
        browser_key=_browser_key(request)
        with transaction.atomic():
            scan=None
            if kind=='personal':
                if not data.get('enrollment_session_id'): raise ValueError
                scan=creator_status(session_id=data['enrollment_session_id'],browser_key=browser_key)
                if not scan.identity_received_at or scan.status!='pending' or scan.claimed_by_id or scan.organization_id:
                    raise EnrollmentError('PC_REGISTRATION_REQUIRED',409)
            owner.set_password(password);owner.save()
            org=Organization.objects.create(name=company_name.strip() if kind=='company' else f'{fio.strip()[:220]} — shaxsiy ish maydoni',
                slug=f'{kind}-{uuid.uuid4().hex}',kind=kind,is_active=kind=='personal',
                approval_status='approved' if kind=='personal' else 'pending',registration_owner=owner)
            owner.organizations.add(org)
            role=Roles.objects.create(organization=org,name='Egasi',created_by=owner)
            Users.objects.create(organization=org,role=role,username=username,fio=fio.strip(),lavozim='Egasi')
            if scan:
                claim(token_hash=scan.token_hash,admin=owner,organization=org,phone_key=browser_key)
                resolve(session_id=scan.id,action='approve',admin=owner,organization=org,phone_key=browser_key,location='Shaxsiy kompyuter')
        login(request,owner,backend='django.contrib.auth.backends.ModelBackend')
        request.session['panel']='admin';request.session['current_org_id']=org.id
        return JsonResponse({'workspace':workspace_data(org),'redirect':'/personal/biometrics' if kind=='personal' else '/registration/status'},status=201)
    except ValidationError as error:
        return JsonResponse({'detail':' '.join(error.messages)},status=400)
    except (ValueError,TypeError):
        return JsonResponse({'detail':'Ma’lumotlarni tekshiring. Shaxsiy hisob uchun PC aniqlanishi shart.'},status=400)
    except IntegrityError:
        return JsonResponse({'detail':'Bu login band yoki ro‘yxatdan o‘tish takrorlangan.'},status=400)
    except EnrollmentError as error:
        return JsonResponse({'detail':error.code},status=error.status)

@require_GET
def registration_status(request):
    if not request.user.is_authenticated: return JsonResponse({'detail':'LOGIN_REQUIRED'},status=401)
    org=request.user.organizations.filter(pk=request.session.get('current_org_id')).first()
    if not org: return JsonResponse({'detail':'NOT_FOUND'},status=404)
    return JsonResponse(workspace_data(org))

@require_GET
def applications(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return JsonResponse({'detail':'Forbidden'},status=403)
    return JsonResponse({'applications':[dict(workspace_data(org),owner=org.registration_owner.username,
        created_at=org.created_at.isoformat()) for org in Organization.objects.select_related('registration_owner').filter(
            kind='company',approval_status='pending',registration_owner__isnull=False).order_by('created_at')]})

@csrf_protect
@require_POST
def decision(request,org_id):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return JsonResponse({'detail':'Forbidden'},status=403)
    try:
        data=json.loads(request.body)
        if not isinstance(data,dict) or data.get('action') not in ['approve','reject']: raise ValueError
        note=data.get('note','')
        if not isinstance(note,str) or len(note)>500: raise ValueError
    except (ValueError,TypeError): return JsonResponse({'detail':'INVALID_REQUEST'},status=400)
    with transaction.atomic():
        org=Organization.objects.select_for_update().filter(pk=org_id,kind='company',registration_owner__isnull=False).first()
        if not org:return JsonResponse({'detail':'NOT_FOUND'},status=404)
        if org.approval_status!='pending':return JsonResponse({'detail':'ALREADY_REVIEWED'},status=409)
        org.approval_status='approved' if data['action']=='approve' else 'rejected'
        org.is_active=data['action']=='approve';org.review_note=note.strip()
        org.reviewed_by=request.user;org.reviewed_at=timezone.now()
        org.save(update_fields=['approval_status','is_active','review_note','reviewed_by','reviewed_at'])
    return JsonResponse(workspace_data(org))
