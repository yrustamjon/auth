import uuid
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.common.permissions import IsWorkspaceAdmin
from apps.common.models import Device
from apps.log.audit import request_snapshot
from .models import AgentEvent, AgentHealth

CLIENT_KINDS={'agent_started','agent_exited','previous_exit_unconfirmed','agent_error','agent_restarted','restart_failed','local_pause_reported','watchdog_started','watchdog_exited','agent_unexpected_exit','restart_attempted'}
LABELS={
    'watchdog_started':'Kuzatuvchi ishga tushdi','watchdog_exited':'Kuzatuvchi chiqish haqida xabar berdi',
    'agent_unexpected_exit':'Kuzatuvchi agent jarayoni kutilmaganda tugaganini aniqladi',
    'restart_attempted':'Kuzatuvchi agentni qayta ishga tushirishga urindi',
    'agent_started':'Agent ishga tushdi','agent_exited':'Agent chiqish haqida xabar berdi',
    'previous_exit_unconfirmed':'Avvalgi agent jarayonining toza yopilgani tasdiqlanmagan',
    'agent_error':'Agent xato haqida xabar berdi','agent_restarted':'Agent qayta ishga tushirilgani xabar qilindi',
    'restart_failed':'Agentni qayta ishga tushirish muvaffaqiyatsizligi xabar qilindi',
    'local_pause_reported':'Mahalliy tanaffus haqida xabar berildi',
    'connection_lost':'Agent bilan aloqa yo‘qoldi — sabab aniqlanmagan',
    'connection_restored':'Agent bilan aloqa tiklandi','pause_authorized':'Administrator tanaffusga ruxsat berdi',
    'pause_expired':'Ruxsatli tanaffus muddati tugadi','pause_cancelled':'Administrator tanaffus ruxsatini bekor qildi',
}
TIMEOUT=timedelta(seconds=120)


def record(device,kind,*,event_id=None,reported_at=None,ip=None,details=None,actor=''):
    row,created=AgentEvent.objects.get_or_create(device_key=device.pk,event_id=event_id or uuid.uuid4(),defaults={
        'organization':device.organization,'device':device,'kind':kind,
        'severity':'warning' if kind in {'connection_lost','previous_exit_unconfirmed','agent_error','restart_failed','agent_unexpected_exit'} else 'info',
        'reported_at':reported_at,'ip_address':ip,'details':details or {},'actor':actor,
        'device_snapshot':{'pc_id':device.pc_id,'platform':device.platform,'location':device.location,'identifiers':device.identifiers}})
    return row,created


def validated_events(payload):
    if not isinstance(payload,dict) or payload.get('state') not in {'running','stopped'}:raise ValueError('Invalid telemetry state')
    if payload.get('reporter','agent') not in {'agent','supervisor'}:raise ValueError('Invalid reporter')
    events=payload.get('events',[])
    if not isinstance(events,list) or len(events)>50:raise ValueError('Invalid event batch')
    validated=[]
    for item in events:
        if not isinstance(item,dict) or item.get('kind') not in CLIENT_KINDS:raise ValueError('Invalid event kind')
        try:
            eid=uuid.UUID(str(item.get('id')))
            reported=parse_datetime(item['reported_at']) if item.get('reported_at') else None
        except (ValueError,TypeError):raise ValueError('Invalid event identity or date') from None
        if reported and timezone.is_naive(reported):raise ValueError('Timezone required')
        details=item.get('details',{})
        if not isinstance(details,dict):raise ValueError('Invalid event details')
        clean={}
        for key in ('pid','previous_pid','exit_code','os_user','reason','agent_version','error_type'):
            value=details.get(key)
            if isinstance(value,str):clean[key]=value[:255]
            elif isinstance(value,int) and not isinstance(value,bool) and -2**63<=value<2**63:clean[key]=value
        validated.append((eid,item['kind'],reported,clean))
    return validated


def check_health(health,now):
    device=health.device
    if health.pause_until:
        if health.pause_until>now:return
        record(device,'pause_expired',details={'pause_until':health.pause_until.isoformat()})
        health.pause_until=None
    if health.state=='running' and now-health.last_heartbeat>TIMEOUT and not health.loss_reported:
        started=AgentEvent.objects.filter(device_key=device.pk,kind='agent_started').order_by('-timestamp','-id').first()
        context={key:started.details[key] for key in ('os_user','pid') if key in started.details} if started else {}
        record(device,'connection_lost',ip=health.last_ip,details={'last_heartbeat':health.last_heartbeat.isoformat(),'detected_at':now.isoformat(),**context})
        health.loss_reported=True
    health.save(update_fields=['pause_until','loss_reported'])


@transaction.atomic
def ingest(request,payload):
    events=validated_events(payload)
    device=request.bioguard_device
    now=timezone.now()
    health,_=AgentHealth.objects.get_or_create(device=device,defaults={'last_heartbeat':now,'state':'unknown'})
    health=AgentHealth.objects.select_for_update().select_related('device__organization').get(pk=health.pk)
    check_health(health,now)
    ip=request_snapshot(request).get('ip_address')
    accepted=[]
    for eid,kind,reported,details in events:
        record(device,kind,event_id=eid,reported_at=reported,ip=ip,details=details)
        accepted.append(str(eid))
    if payload.get('reporter','agent')=='agent':
        if health.loss_reported and payload['state']=='running':record(device,'connection_restored',ip=ip)
        health.last_heartbeat=now;health.last_ip=ip;health.state=payload['state'];health.loss_reported=False
        health.save(update_fields=['last_heartbeat','last_ip','state','loss_reported'])
    return {'accepted':accepted,'pause_until':health.pause_until,'heartbeat_seconds':30}


def detect_missing(org_id=None):
    query=AgentHealth.objects.filter(device__is_active=True,device__organization__is_active=True,device__removal_state='active')
    if org_id is not None:query=query.filter(device__organization_id=org_id)
    for pk in query.values_list('pk',flat=True):
        with transaction.atomic():
            health=AgentHealth.objects.select_for_update().select_related('device__organization').filter(pk=pk).first()
            if health:check_health(health,timezone.now())


class TelemetryView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]
    def post(self,request):
        if not getattr(request,'bioguard_device',None):return Response({'detail':'Signed device required'},status=401)
        try:return Response(ingest(request,request.data))
        except ValueError as error:return Response({'detail':str(error)},status=400)


class SupervisionPolicyView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]
    def get(self,request):
        device=getattr(request,'bioguard_device',None)
        if not device:return Response({'detail':'Signed device required'},status=401)
        health=AgentHealth.objects.filter(device=device).first()
        now=timezone.now()
        return Response({'allowed':device.is_active and not device.revoked_at and device.removal_state=='active',
            'pause_until':health.pause_until if health and health.pause_until and health.pause_until>now else None},headers={'Cache-Control':'no-store'})


class AgentEventsView(APIView):
    permission_classes=[IsWorkspaceAdmin]
    def get(self,request):
        org=request.session.get('current_org_id');detect_missing(org)
        rows=AgentEvent.objects.filter(organization_id=org).order_by('-timestamp','-id')[:300]
        devices=Device.objects.filter(organization_id=org,removal_state='active').select_related('agent_health').order_by('pc_id','pk')
        device_list=[]
        for device in devices:
            health=getattr(device,'agent_health',None)
            device_list.append({'id':device.pk,'pc_id':device.pc_id,
                'last_heartbeat':health.last_heartbeat if health else None,
                'state':health.state if health else 'not_reporting',
                'pause_until':health.pause_until if health else None})
        return Response({'devices':device_list,
            'events':[{'id':row.pk,'kind':row.kind,'title':LABELS.get(row.kind,row.kind),'severity':row.severity,
            'timestamp':row.timestamp,'reported_at':row.reported_at,'device_pc_id':row.device_snapshot.get('pc_id'),
            'device_snapshot':row.device_snapshot,'ip_address':row.ip_address,'details':row.details,'actor':row.actor,
            'origin':'administrator' if row.actor else 'agent_report' if row.kind in CLIENT_KINDS else 'server'} for row in rows]})


class PausePermissionView(APIView):
    permission_classes=[IsWorkspaceAdmin]
    def post(self,request,device_id):
        minutes=request.data.get('minutes');reason=request.data.get('reason','')
        if type(minutes) is not int or not 0<=minutes<=240 or not isinstance(reason,str) or not reason.strip() or len(reason)>255:
            return Response({'detail':'Sabab va 0–240 daqiqa kiriting'},status=400)
        with transaction.atomic():
            device=Device.objects.select_for_update().filter(pk=device_id,organization_id=request.session.get('current_org_id'),removal_state='active').first()
            if not device:return Response({'detail':'Device not found'},status=404)
            now=timezone.now();health,_=AgentHealth.objects.get_or_create(device=device,defaults={'last_heartbeat':now,'state':'unknown'})
            health.pause_until=now+timedelta(minutes=minutes) if minutes else None
            health.save(update_fields=['pause_until'])
            record(device,'pause_authorized' if minutes else 'pause_cancelled',actor=request.user.username,
                details={'reason':reason.strip(),'pause_until':health.pause_until.isoformat() if health.pause_until else None})
        return Response({'pause_until':health.pause_until})
