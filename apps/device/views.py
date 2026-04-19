from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny


from apps.common.models import *


class DeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.session.get("current_org_id")
        devices = Device.objects.filter(organization_id=org).all()

        return Response([
            {
                "id": device.id,
                "pc_id": device.pc_id,
                "license": device.license,
                "location": device.location,
                "last_seen": device.last_seen,
                "is_active": device.is_active,
                "registered_at": device.registered_at,
                "device_public_key": device.device_public_key
            } for device in devices
        ])

    def post(self, request):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        pc_id    = request.data.get("pc_id")
        location = request.data.get("location")
        license  = request.data.get("license")
        print(pc_id,license)

        if not pc_id or not location or not license:
            return Response({"detail": "pc_id, location va license majburiy."}, status=400)

        device = Device.objects.create(
            organization_id=org.id,
            pc_id=pc_id,
            location=location,
            license=license
        )
        i=device
        print(i.pc_id,i.license )

        return Response({"ok": True}, status=201)
        
    def put(self, request, device_id):
        print(request.data)
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        device = Device.objects.filter(id=device_id, organization_id=org.id).first()
        if not device:
            return Response({"error": "Device not found"}, status=404)

        device.pc_id = request.data.get("pc_id", device.pc_id)
        device.is_active = request.data.get("is_active", device.is_active)
        device.location = request.data.get("location", device.location)
        pub_key = request.data.get("device_public_key")

        if pub_key is not None:
            device.device_public_key = pub_key
        
        device.save()

        return Response({"ok": True})
    
    def patch(self, request, device_id):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        device = Device.objects.filter(id=device_id, organization_id=org.id).first()
        print(request.data)
        if not device:
            return Response({"error": "Device not found"}, status=404)
        
        if "is_active" in request.data:
            device.is_active = request.data.get("is_active", device.is_active)
        
        print(request.data.get("revoked"))
        device.save()
        return Response({"ok": True})
    
    def delete(self, request, device_id):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        device = Device.objects.filter(id=device_id, organization_id=org.id).first()
        if not device:
            return Response({"error": "Device not found"}, status=404)
        
        device.delete()
        return Response({"ok": True})


class DeviceCheck(APIView):
    permission_classes =[AllowAny]
    def post(self,request):
        # {'device_uuid': 'b1806902-e17b-4ae4-a505-ba79e4f1595e', 'windows_license': '00331-10000-00001-AA904'}
        device = Device.objects.filter(pc_id=request.data['device_uuid'],license=request.data['windows_license'])
        print([(i.pc_id,i.license )for i in Device.objects.all()],device)

        if not device:
            return Response({"error": "Device not found"}, status=404)
        
        return Response({
            'ok':True
        })