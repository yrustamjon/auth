"""Historical access records: snapshot identities rather than mutable relations."""
from copy import deepcopy
from ipaddress import ip_address
from math import isfinite
from django.conf import settings
from apps.common.models import AccessLogs
from .similarity import log_similarity


def valid_ip(value):
    try:
        return str(ip_address(value))
    except (ValueError, TypeError):
        return None


def client_snapshot(info):
    if not isinstance(info, dict):
        return {}
    result={}
    for key in ('user_agent','browser','browser_version','platform','platform_version','language','timezone','device_type'):
        value=info.get(key)
        if isinstance(value,str):result[key]=value[:1024]
    for key in ('screen','viewport'):
        value=info.get(key)
        if isinstance(value,dict):
            result[key]={k:v for k,v in value.items() if k in ('width','height','pixel_ratio','color_depth') and isinstance(v,(int,float)) and not isinstance(v,bool) and isfinite(v) and 0<=v<=100000}
    if isinstance(info.get('mobile'),bool):result['mobile']=info['mobile']
    return result


def request_snapshot(request, client_info=None):
    if request is None:return {}
    peer=valid_ip(request.META.get('REMOTE_ADDR'))
    address=peer
    # Forwarded headers are authoritative only behind an explicitly trusted peer.
    if peer in getattr(settings,'AUDIT_TRUSTED_PROXY_IPS',[]):
        forwarded=request.META.get('HTTP_X_FORWARDED_FOR','').split(',')[-1].strip()
        address=valid_ip(forwarded) or peer
    return {'ip_address':address,'peer_ip':peer,'method':request.method,'path':request.path[:512],
        'user_agent':request.META.get('HTTP_USER_AGENT','')[:2048],
        'accept_language':request.META.get('HTTP_ACCEPT_LANGUAGE','')[:256],
        'browser_hints':{key:request.META.get(header,'')[:512] for key,header in (
            ('brands','HTTP_SEC_CH_UA'),('platform','HTTP_SEC_CH_UA_PLATFORM'),('mobile','HTTP_SEC_CH_UA_MOBILE'))},
        'client':client_snapshot(client_info)}


def write_access_log(session,device,success,cause='',*,request=None,similarity=None,client_info=None):
    context=request_snapshot(request,client_info)
    if session.request_context:
        context['initiator']=deepcopy(session.request_context)
    score=similarity if similarity is not None else log_similarity(cause)
    if score is not None:
        score=float(score)
        if not isfinite(score) or not 0<=score<=1:score=None
    user=session.user
    return AccessLogs.objects.create(organization=device.organization,user=user,device=device,success=success,
        cause=cause[:255],similarity=score,ip_address=context.get('ip_address'),
        source='mobile_web' if request and '/phone/' in request.path else 'desktop_agent',
        user_snapshot={'id':user.pk,'username':user.username,'fio':user.fio},
        device_snapshot={'id':device.pk,'pc_id':device.pc_id,'platform':device.platform,'location':device.location,
            'identifiers':deepcopy(device.identifiers),'enrollment_status':device.enrollment_status,
            'attestation_status':device.attestation_status,'is_active':device.is_active,'last_ip':device.last_ip,
            'registered_at':device.registered_at.isoformat() if device.registered_at else None,
            'enrolled_at':device.enrolled_at.isoformat() if device.enrolled_at else None},request_context=context)


def serialize_log(log):
    user=log.user_snapshot or {}
    device=log.device_snapshot or {}
    return {'id':log.pk,'timestamp':log.timestamp,'success':log.success,'cause':log.cause,
        'similarity':log.similarity if log.similarity is not None else log_similarity(log.cause),
        'user_fio':user.get('fio') or (log.user.fio if log.user else "Noma'lum"),
        'username':user.get('username') or (log.user.username if log.user else ''),
        'device_pc_id':device.get('pc_id') or (log.device.pc_id if log.device else "Noma'lum"),
        'ip_address':log.ip_address,'source':log.source,'user_snapshot':user,
        'device_snapshot':device,'request_context':log.request_context}
