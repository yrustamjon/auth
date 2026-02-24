from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.models import *

# timestamp, user, device, success, cause

class LogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.session.get("current_org_id")
        query = request.query_params
        try:
            if query:
                start_date = query.get("start_date")
                end_date = datetime.now()
                logs = AccessLogs.objects.filter(
                    organization_id=org,
                    timestamp__range=[start_date, end_date]
                ).order_by("-timestamp").all()
                print(logs)
            else:
                logs = AccessLogs.objects.filter(organization_id=org).order_by("-timestamp").all()
                print(logs)
        except Exception as e:
            try:
                if query.get("start_date"):
                    start_date = query.get("start_date")
                    logs = AccessLogs.objects.filter(
                        organization_id=org,
                        timestamp__gte=start_date
                    ).order_by("-timestamp").all()
                    print(logs)
                else:
                    logs = AccessLogs.objects.filter(organization_id=org).order_by("-timestamp").all()
                    print(logs)
            except Exception as e2:
                print(f"Error filtering logs: {e2}")
        
        data=[
            {
                "id":           log.id,
                "timestamp":    log.timestamp,
                "success":      log.success,
                "cause":        log.cause,
                "user_fio":     log.user.fio      if log.user   else "Noma'lum",
                "device_pc_id": log.device.pc_id  if log.device else "Noma'lum",
            } for log in logs
        ]
        return Response({"logs": data})
