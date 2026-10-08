from django.db import transaction
from django.utils import timezone

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.models import AdminUser, Device, Organization
from apps.org.models import OrgToken

import uuid
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


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
        from django.db import OperationalError
        try:
            return self._activate(request)
        except OperationalError:
            return Response({'detail': 'Enrollment database busy; retry'}, status=503)

    def _activate(self, request):
        token = request.data.get("token") or request.data.get("activation_code")
        device_uuid = request.data.get("device_uuid")
        license_key = request.data.get("license") or request.data.get("windows_license")
        public_key = request.data.get("public_key")

        if not all(isinstance(v, str) and v.strip() and len(v) <= limit
                   for v, limit in ((token, 255), (device_uuid, 255), (license_key, 255), (public_key, 16384))):
            return Response({"error": "Missing fields"}, status=400)

        try:
            key = serialization.load_pem_public_key(public_key.encode())
            if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
                raise ValueError('RSA >=2048 required')
        except (ValueError, TypeError, UnsupportedAlgorithm):
            return Response({'detail': 'Invalid public key: RSA >=2048 required'}, status=400)

        from apps.agent.security import verify_bootstrap, AuthenticationFailure
        try:
            verify_bootstrap(request, {'public_key':public_key, 'device_uuid':device_uuid})
        except AuthenticationFailure as error:
            return Response({'detail':'Bootstrap proof rejected'},status=error.status)

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
                device = Device.objects.select_for_update().get(
                    pc_id=device_uuid,
                    organization=org_token.org,
                )
            except Device.DoesNotExist:
                return Response({"error": "Device not registered"}, status=400)

            if not org_token.org.is_active or device.revoked_at is not None:
                return Response({'detail': 'Organization inactive or device revoked'}, status=403)
            browser_pending = device.enrollment_status == Device.EnrollmentStatus.BROWSER_APPROVED
            if device.cert or device.device_public_key:
                return Response({'detail': 'Device already enrolled'}, status=409)
            if not device.is_active and not browser_pending:
                return Response({'detail': 'Device inactive'}, status=403)
            if device.license != license_key and not (browser_pending and device.license == 'UNKNOWN'):
                return Response({"error": "License mismatch"}, status=400)

            # Conditional write is the final claim: row locks alone are not supported by SQLite.
            if OrgToken.objects.filter(pk=org_token.pk, is_used=False, expires_at__gt=timezone.now()).update(is_used=True) != 1:
                return Response({'detail': 'Token already consumed or expired'}, status=409)
            cert = str(uuid.uuid4())
            device.license = license_key
            if device.platform == Device.Platform.WINDOWS:
                device.identifiers = {**device.identifiers, 'product_id': license_key}
            device.enrollment_status = Device.EnrollmentStatus.AGENT_ENROLLED
            device.enrolled_at = timezone.now()

            device.cert = cert
            device.device_public_key = public_key
            device.is_active = True
            device.save()


        return Response({
            "certificate": {
                "cert_id": cert,
                "org_slug": org_token.org.slug,
                "pc_id": device.pc_id,
            },
            "org_slug": org_token.org.slug,
            "message": "Activated",
        })
