from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.permissions import IsWorkspaceAdmin

from apps.common.models import AccessLogs
from .audit import serialize_log

# timestamp, user, device, success, cause

class LogView(APIView):
    permission_classes = [IsWorkspaceAdmin]

    def get(self, request):
        logs=AccessLogs.objects.filter(organization_id=request.session.get('current_org_id')).select_related('user','device').order_by('-timestamp')
        start=request.query_params.get('start_date')
        if start:
            try:value=parse_datetime(start) or parse_date(start)
            except ValueError:value=None
            if value is None:return Response({'detail':'start_date formati noto‘g‘ri'},status=400)
            logs=logs.filter(timestamp__gte=value)
        return Response({"logs": [serialize_log(log) for log in logs]})
