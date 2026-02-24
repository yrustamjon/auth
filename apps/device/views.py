from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from apps.common.models import *


class DeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.session.get("current_org_id")
        devices = Devices.objects.filter(organization_id=org).all()

        return Response([
            {
                "id": device.id,
                "pc_id": device.pc_id,
                "location": device.location,
                "last_seen": device.last_seen,
                "revoked": device.revoked,
                "is_active": device.is_active,
                "registered_at": device.registered_at,
                "device_public_key": device.device_public_key
            } for device in devices
        ])

    def post(self, request):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        pc_id = request.data.get("pc_id")
        location = request.data.get("location")

        device = Devices.objects.create(
            organization_id=org.id,
            pc_id=pc_id,
            location=location
        )

        return Response({"ok": True})
    
    def put(self, request, device_id):
        print(request.data)
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        device = Devices.objects.filter(id=device_id, organization_id=org.id).first()
        if not device:
            return Response({"error": "Device not found"}, status=404)

        device.pc_id = request.data.get("pc_id", device.pc_id)
        device.is_active = request.data.get("is_active", device.is_active)
        device.revoked = request.data.get("revoked", device.revoked)
        pub_key = request.data.get("device_public_key")
        if pub_key is not None:
            device.device_public_key = pub_key
        
        device.save()

        return Response({"ok": True})
    
    def patch(self, request, device_id):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        device = Devices.objects.filter(id=device_id, organization_id=org.id).first()
        print(request.data)
        if not device:
            return Response({"error": "Device not found"}, status=404)
        
        if "is_active" in request.data:
            device.is_active = request.data.get("is_active", device.is_active)
        if "revoked" in request.data:
            device.revoked = request.data.get("revoked", device.revoked)
        print(device.revoked, request.data.get("revoked"))
        device.save()
        return Response({"ok": True})
    
    def delete(self, request, device_id):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        device = Devices.objects.filter(id=device_id, organization_id=org.id).first()
        if not device:
            return Response({"error": "Device not found"}, status=404)
        
        device.delete()
        return Response({"ok": True})
    