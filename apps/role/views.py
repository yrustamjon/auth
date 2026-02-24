from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.models import *

class RoleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.session.get("current_org_id")
        roles= Roles.objects.filter(organization_id=org)

        return Response([
            {
                "id": role.id,
                "name": role.name,
                "created_at": role.created_at,
                "is_active": role.is_active
            } for role in roles
        ])
    
    def post(self, request):
        print("Creating role with data:", request.data)
        org = request.session.get("current_org_id")
        role = Roles.objects.create(
            organization_id=org,
            name=request.data.get("name"),
            created_by_id=request.user.id
        )

        return Response({"ok": True})
    
    def patch(self, request, id):
        role = Roles.objects.filter(id=id).first()
        print("Updating role with id", id, "data:", request.data)
        print(role.is_active)
        if not role:
            return Response({"detail": "Role not found"}, status=404)
        if "name"  in request.data:
            role.name = request.data.get("name", role.name)
        else:
            role.is_active = request.data.get("is_active")
        role.save()

        return Response({"ok": True})
    
    def delete(self, request, id):
        role = Roles.objects.filter(id=id).first()
        if not role:
            return Response({"detail": "Role not found"}, status=404)
        role.delete()

        return Response({"ok": True})