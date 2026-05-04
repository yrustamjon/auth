from django.db import transaction
from django.utils import timezone

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.models import AdminUser, Device, Organization
from apps.org.models import OrgToken

import uuid


# =========================
# SWITCH ORG
# =========================
class SwitchOrganization(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        org_id = request.data.get("organization_id")

        if not org_id:
            return Response({"detail": "organization_id required"}, status=400)

        if not request.user.organizations.filter(id=org_id).exists():
            return Response({"detail": "Forbidden"}, status=403)

        request.session["current_org_id"] = org_id
        request.session.save()

        return Response({"ok": True})


# =========================
# ORGANIZATIONS CRUD
# =========================
class Organizations(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        if id:
            org = Organization.objects.filter(id=id).first()
            if not org:
                return Response({"detail": "Not found"}, status=404)

            return Response({
                "id": org.id,
                "name": org.name,
                "admin_count": AdminUser.objects.filter(organizations=org).count(),
                "slug": org.slug,
                "active": org.is_active,
                "created_at": org.created_at,
            })

        orgs = Organization.objects.exclude(slug="system")

        return Response([
            {
                "id": org.id,
                "name": org.name,
                "admin_count": AdminUser.objects.filter(organizations=org).count(),
                "slug": org.slug,
                "active": org.is_active,
                "created_at": org.created_at,
            }
            for org in orgs
        ])

    def post(self, request):
        name = request.data.get("name")
        slug = request.data.get("slug")

        if not name or not slug:
            return Response({"detail": "Name and slug required"}, status=400)

        if Organization.objects.filter(slug=slug).exists():
            return Response({"detail": "Slug exists"}, status=400)

        org = Organization.objects.create(name=name, slug=slug)

        return Response({
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "active": org.is_active,
            "created_at": org.created_at,
        })

    def patch(self, request, id):
        org = Organization.objects.filter(id=id).first()
        if not org:
            return Response({"detail": "Not found"}, status=404)

        name = request.data.get("name")
        slug = request.data.get("slug")
        active = request.data.get("active")

        if name:
            org.name = name
        if slug:
            org.slug = slug
        if active is not None:
            org.is_active = active

        org.save()
        return Response({"ok": True})

    def delete(self, request, id):
        org = Organization.objects.filter(id=id).first()
        if not org:
            return Response({"detail": "Not found"}, status=404)

        org.delete()
        return Response({"ok": True})


# =========================
# GET ACTIVE TOKEN (AUTH REQUIRED)
# =========================
class GetActiveToken(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org_id = request.session.get("current_org_id")

        if not org_id:
            return Response({"error": "No org selected"}, status=400)

        if not request.user.organizations.filter(id=org_id).exists():
            return Response({"detail": "Forbidden"}, status=403)

        token = OrgToken.get_or_create_active_for_org(org_id)

        return Response({
            "token": token.token,
            "expires_at": token.expires_at,
        })


# =========================
# ACTIVATE AGENT (NO AUTH)
# =========================
class ActivateAgent(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token") or request.data.get("activation_code")
        device_uuid = request.data.get("device_uuid")
        license_key = request.data.get("license") or request.data.get("windows_license")
        public_key = request.data.get("public_key")

        if not all([token, device_uuid, license_key, public_key]):
            return Response({"error": "Missing fields"}, status=400)

        with transaction.atomic():
            org_token = OrgToken.objects.select_for_update().filter(
                token=token,
                is_used=False,
            ).first()

            if not org_token:
                return Response({"error": "Invalid token"}, status=400)

            if org_token.expires_at < timezone.now():
                return Response({"error": "Token expired"}, status=400)

            try:
                device = Device.objects.get(
                    pc_id=device_uuid,
                    organization=org_token.org,
                )
            except Device.DoesNotExist:
                return Response({"error": "Device not registered"}, status=400)

            if device.license != license_key:
                return Response({"error": "License mismatch"}, status=400)

            cert = str(uuid.uuid4())

            device.cert = cert
            device.device_public_key = public_key
            device.is_active = True
            device.save()

            org_token.is_used = True
            org_token.save(update_fields=["is_used"])

        return Response({
            "certificate": {
                "cert_id": cert,
                "org_slug": org_token.org.slug,
                "pc_id": device.pc_id,
            },
            "org_slug": org_token.org.slug,
            "message": "Activated",
        })
