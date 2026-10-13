import secrets
from datetime import timedelta

from django.db import IntegrityError, OperationalError, transaction
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from apps.agent.security import AuthenticationFailure
from apps.common.models import Device, Organization
from apps.common.permissions import IsWorkspaceAdmin
from .models import DeviceRemovalCode
from . import removal
from apps.agent.security import consume_nonce, verify_signature


class RemovalThrottle(SimpleRateThrottle):
    scope = 'device_removal'
    rate = '30/min'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class IssueRemovalCode(APIView):
    permission_classes = [IsWorkspaceAdmin]

    def post(self, request, device_id):
        code = secrets.token_urlsafe(32)
        now = timezone.now()
        try:
            with transaction.atomic():
                device = Device.objects.select_for_update().select_related('organization').filter(
                    pk=device_id, organization_id=request.session.get('current_org_id')).first()
                if device is None:
                    return Response({'detail': 'NOT_FOUND'}, status=404)
                if device.organization.kind == Organization.Kind.PERSONAL and device.organization.registration_owner_id != request.user.pk:
                    return Response({'detail': 'OWNER_REQUIRED'}, status=403)
                if device.removal_state != 'active' or device.revoked_at or not device.organization.is_active:
                    return Response({'detail': 'REMOVAL_ALREADY_STARTED'}, status=409)
                DeviceRemovalCode.objects.filter(device=device, used_at__isnull=True).update(invalidated_at=now)
                record = DeviceRemovalCode.objects.create(device=device, issuer=request.user,
                    certificate_generation=device.cert or '', code_digest=removal.digest(code),
                    expires_at=now + timedelta(minutes=10))
        except (OperationalError, IntegrityError):
            return Response({'detail': 'REMOVAL_STATE_BUSY'}, status=409)
        return Response({'code': code, 'expires_at': record.expires_at.isoformat(),
            **removal.summary(device)}, status=201, headers={'Cache-Control': 'no-store'})


class RemovalAction(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RemovalThrottle]
    action = None

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response({'detail': 'INVALID_REQUEST'}, status=400)
        try:
            result = getattr(removal, self.action)(request._request, request.data)
            return Response(result, headers={'Cache-Control': 'no-store'})
        except removal.RemovalError as error:
            return Response({'detail': error.code}, status=error.status)
        except AuthenticationFailure as error:
            return Response({'detail': 'REMOVAL_PROOF_REJECTED'}, status=error.status)
        except (OperationalError, IntegrityError):
            return Response({'detail': 'REMOVAL_STATE_BUSY'}, status=409)


class InstallStatus(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        device = request._request.bioguard_device
        return Response({**removal.summary(device), 'certificate_id': device.cert})


class ActivationStatus(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RemovalThrottle]

    def post(self, request):
        try:
            if not isinstance(request.data, dict):
                raise removal.RemovalError('INVALID_REQUEST', 400)
            key = removal.public_key(request.data.get('public_key'))
            device_uuid = request.data.get('device_uuid')
            if not isinstance(device_uuid, str) or not 1 <= len(device_uuid) <= 255:
                raise removal.RemovalError('INVALID_DEVICE', 400)
            nonce, expiry = verify_signature(request._request, key, device_uuid, 'bootstrap')
            device = Device.objects.select_related('organization').filter(pc_id=device_uuid,
                device_public_key=key, revoked_at__isnull=True, is_active=True,
                organization__is_active=True, enrollment_status=Device.EnrollmentStatus.AGENT_ENROLLED,
                removal_state='active').first()
            if not device or not device.cert:
                return Response({'detail': 'ENROLLMENT_NOT_FOUND'}, status=404)
            if not consume_nonce('activation-recovery:' + device.cert, nonce, expiry):
                raise AuthenticationFailure(409)
            return Response({'certificate': {'cert_id': device.cert,
                'org_slug': device.organization.slug, 'pc_id': device.pc_id}}, headers={'Cache-Control': 'no-store'})
        except removal.RemovalError as error:
            return Response({'detail': error.code}, status=error.status)
        except AuthenticationFailure as error:
            return Response({'detail': 'BOOTSTRAP_PROOF_REJECTED'}, status=error.status)
        except OperationalError:
            return Response({'detail': 'ENROLLMENT_STATE_BUSY'}, status=503)
