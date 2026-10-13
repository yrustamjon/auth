from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsWorkspaceAdmin
from .models import Organization, Users, Device, AccessLogs, BiometricFace, BiometricFingerprint
from apps.log.audit import serialize_log

class PersonalProfile(APIView):
    permission_classes = [IsWorkspaceAdmin]

    def get(self,request):
        org=Organization.objects.filter(pk=request.session.get('current_org_id'),kind='personal',registration_owner=request.user).first()
        if not org:return Response({'detail':'Forbidden'},status=403)
        user=Users.objects.filter(organization=org,username=request.user.username).first()
        if not user:return Response({'detail':'Personal profile not found'},status=404)
        return Response({
            'user':{'id':user.id,'fio':user.fio,'username':user.username,
                'has_face':BiometricFace.objects.filter(user=user).exists(),
                'has_fingerprint':BiometricFingerprint.objects.filter(user=user).exists()},
            'devices':list(Device.objects.filter(organization=org).values('id','pc_id','platform','location','enrollment_status','is_active','last_seen','removal_state','agent_allocation_active')),
            'logs':[serialize_log(row)
                for row in AccessLogs.objects.filter(organization=org,user=user).select_related('device').order_by('-timestamp')[:100]],
        })
