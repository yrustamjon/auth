from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny


from apps.common.models import *


def _platform_or_error(value):
    platform = value or Device.Platform.WINDOWS
    if platform not in Device.Platform.values:
        return None
    return platform


def _identifiers_or_error(value, platform, pc_id, license_value):
    if value is None:
        return {}
    if not isinstance(value, dict):
        return None
    allowed = {
        Device.Platform.WINDOWS: {"machine_guid", "product_id"},
        Device.Platform.MACOS: {"platform_uuid", "serial"},
        Device.Platform.LINUX: {"machine_id", "product_uuid"},
    }[platform]
    if set(value) - allowed or any(
        not isinstance(item, str) or not item.strip() or len(item.strip()) > 255
        for item in value.values()
    ):
        return None
    if value and set(value) != allowed:
        return None
    identifiers = {key: item.strip() for key, item in value.items()}
    if platform == Device.Platform.WINDOWS and (
        identifiers.get("machine_guid", pc_id) != pc_id
        or identifiers.get("product_id", license_value) != license_value
    ):
        return None
    return identifiers


class DeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.session.get("current_org_id")
        devices = Device.objects.filter(organization_id=org).all()

        return Response([
            {
                "id": device.id,
                "pc_id": device.pc_id,
                "device_id": device.device_id,
                "license": device.license,
                "identifiers": device.identifiers,
                "enrollment_status": device.enrollment_status,
                "location": device.location,
                "last_seen": device.last_seen,
                "is_active": device.is_active,
                "registered_at": device.registered_at,
                "device_public_key": device.device_public_key,
                "public_key": device.public_key,
                "platform": device.platform,
            } for device in devices
        ])

    def post(self, request):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        pc_id    = request.data.get("pc_id") or request.data.get("device_id")
        location = request.data.get("location")
        license  = request.data.get("license")
        platform = _platform_or_error(request.data.get("platform"))
        if platform is None:
            return Response({"detail": "Invalid platform"}, status=400)
        if platform != Device.Platform.WINDOWS and not license:
            license = "UNKNOWN"
        if not pc_id or not location or not license:
            return Response({"detail": "pc_id, location va license majburiy."}, status=400)
        identifiers = _identifiers_or_error(
            request.data.get("identifiers"), platform, pc_id, license
        )
        if identifiers is None:
            return Response({"detail": "Invalid identifiers"}, status=400)

        device = Device.objects.create(
            organization_id=org.id,
            pc_id=pc_id,
            location=location,
            license=license,
            platform=platform,
            identifiers=identifiers,
        )

        return Response({"ok": True}, status=201)
        
    def put(self, request, device_id):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        device = Device.objects.filter(id=device_id, organization_id=org.id).first()
        if not device:
            return Response({"error": "Device not found"}, status=404)
        if device.enrollment_status == Device.EnrollmentStatus.BROWSER_APPROVED:
            return Response({"error": "Agent enrollment required"}, status=409)

        new_pc_id = request.data.get("pc_id", request.data.get("device_id", device.pc_id))
        new_platform = device.platform
        if "platform" in request.data:
            new_platform = _platform_or_error(request.data.get("platform"))
            if new_platform is None:
                return Response({"detail": "Invalid platform"}, status=400)
        new_license = request.data.get("license", device.license)
        if new_platform != Device.Platform.WINDOWS and not new_license:
            new_license = "UNKNOWN"
        if not new_license:
            return Response({"detail": "license majburiy."}, status=400)
        identifiers = _identifiers_or_error(
            request.data.get("identifiers", device.identifiers),
            new_platform,
            new_pc_id,
            new_license,
        )
        if identifiers is None:
            return Response({"detail": "Invalid identifiers"}, status=400)
        device.pc_id = new_pc_id
        device.license = new_license
        device.is_active = request.data.get("is_active", device.is_active)
        device.location = request.data.get("location", device.location)
        device.platform = new_platform
        device.identifiers = identifiers
        pub_key = request.data.get("public_key", request.data.get("device_public_key"))

        if pub_key is not None:
            device.device_public_key = pub_key
        
        device.save()

        return Response({"ok": True})
    
    def patch(self, request, device_id):
        org = Organization.objects.get(id=request.session.get("current_org_id"))
        device = Device.objects.filter(id=device_id, organization_id=org.id).first()
        if not device:
            return Response({"error": "Device not found"}, status=404)
        if device.enrollment_status == Device.EnrollmentStatus.BROWSER_APPROVED:
            return Response({"error": "Agent enrollment required"}, status=409)
        
        if "is_active" in request.data:
            device.is_active = request.data.get("is_active", device.is_active)
        
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
    permission_classes = [AllowAny]

    def post(self,request):
        device=request.bioguard_device
        if request.data.get('device_uuid') != device.pc_id or request.data.get('windows_license') != device.license:
            return Response({'detail':'Device identity mismatch'},status=404)
        return Response({'ok':True})
