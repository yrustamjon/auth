from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class SwitchOrganization(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("SwitchOrganization request data:", request.data)
        org_id = request.data.get("organization_id")

        
        if not request.user.organizations.filter(id=org_id).exists():
            return Response({"detail": "Forbidden"}, status=403)


        request.session["current_org_id"] = org_id
        request.session.save()

        return Response({"ok": True})