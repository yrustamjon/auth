from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.models import *

class RoleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.session.get("current_org_id")
        roles= Role.objects.filter(organization_id=org)

        return Response({
            "roles": roles
            })
    
    def post(self, request):
        org = request.session.get("current_org_id")
        role = Role.objects.create(
            organization_id=org,
            name=request.data.get("name"),
            created_by_id=request.user.id
        )

        return Response({
            "id": role.id,
            "name": role.name,
            "created_at": role.created_at,
        })