"""Device-specific online removal; normal authentication never accepts revoked keys."""
import hashlib
import hmac
import uuid
from datetime import timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.exceptions import UnsupportedAlgorithm
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.agent.models import AgentSession
from apps.agent.security import AuthenticationFailure, consume_nonce, verify_signature
from apps.common.models import Device
from .models import DeviceRemoval, DeviceRemovalCode


class RemovalError(Exception):
    def __init__(self, code, status=403):
        self.code, self.status = code, status
        super().__init__(code)


def digest(code):
    return hmac.new(settings.SECRET_KEY.encode(), ('device-removal-v1:' + code).encode(), hashlib.sha256).hexdigest()


def public_key(value):
    try:
        if not isinstance(value, str) or len(value) > 16384:
            raise ValueError
        key = serialization.load_pem_public_key(value.encode())
        if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
            raise ValueError
        return key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    except (ValueError, TypeError, UnsupportedAlgorithm):
        raise RemovalError('INVALID_RECOVERY_KEY', 400) from None


def operation_id(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise RemovalError('INVALID_OPERATION', 400) from None


def code_record(payload):
    code = payload.get('code')
    if not isinstance(code, str) or not 20 <= len(code) <= 128:
        raise RemovalError('INVALID_REMOVAL_CODE')
    row = DeviceRemovalCode.objects.select_related('device__organization', 'issuer').filter(
        code_digest=digest(code), used_at__isnull=True, invalidated_at__isnull=True,
        expires_at__gt=timezone.now()).first()
    if not row or payload.get('device_uuid') != row.device.pc_id:
        raise RemovalError('INVALID_REMOVAL_CODE')
    device = row.device
    if row.certificate_generation != (device.cert or ''):
        raise RemovalError('ENROLLMENT_CHANGED')
    issuer = row.issuer
    if not issuer or not issuer.is_active or not (issuer.is_admin or issuer.is_superadmin) or not issuer.organizations.filter(pk=device.organization_id).exists():
        raise RemovalError('ISSUER_NO_LONGER_AUTHORIZED')
    if device.organization.kind == 'personal' and device.organization.registration_owner_id != issuer.pk:
        raise RemovalError('OWNER_REQUIRED')
    if device.removal_state != 'active' or device.revoked_at or not device.organization.is_active:
        raise RemovalError('DEVICE_NOT_REMOVABLE')
    return row


def verify(request, key, device_uuid, certificate):
    nonce, expires = verify_signature(request, key, device_uuid, certificate)
    if not consume_nonce(certificate, nonce, expires):
        raise AuthenticationFailure(409)


def verify_code_request(request, payload, row):
    device = row.device
    certificate = request.headers.get('X-Cert-ID')
    if certificate == 'removal-bootstrap':
        # Admin-issued device-specific code plus proof of the recovery key also
        # permits repair/removal when the old local credential bundle is lost.
        key = public_key(payload.get('recovery_public_key'))
        verify(request, key, device.pc_id, 'removal-bootstrap')
    else:
        if not device.cert or not device.device_public_key:
            raise AuthenticationFailure()
        verify(request, device.device_public_key, device.pc_id, device.cert)


def summary(device):
    return {'device_uuid': device.pc_id, 'organization': device.organization.name,
        'workspace_kind': device.organization.kind, 'state': device.removal_state}


def check(request, payload):
    row = code_record(payload)
    verify_code_request(request, payload, row)
    return summary(row.device)


def begin(request, payload):
    oid = operation_id(payload.get('operation_id'))
    recovery = public_key(payload.get('recovery_public_key'))
    # A lost begin response is recovered with status and the pre-persisted key.
    if DeviceRemoval.objects.filter(pk=oid).exists():
        raise RemovalError('RECOVER_EXISTING_OPERATION', 409)
    row = code_record(payload)
    verify_code_request(request, payload, row)
    now = timezone.now()
    with transaction.atomic():
        device = Device.objects.select_for_update().select_related('organization').get(pk=row.device_id)
        if row.certificate_generation != (device.cert or ''):
            raise RemovalError('ENROLLMENT_CHANGED', 409)
        if device.removal_state != 'active' or device.revoked_at:
            raise RemovalError('DEVICE_NOT_REMOVABLE', 409)
        claimed = DeviceRemovalCode.objects.filter(pk=row.pk, used_at__isnull=True,
            invalidated_at__isnull=True, expires_at__gt=now).update(used_at=now)
        if claimed != 1:
            raise RemovalError('CODE_ALREADY_CLAIMED', 409)
        DeviceRemoval.objects.create(id=oid, device=device, issuer=row.issuer,
            old_certificate=device.cert or '', old_public_key=device.device_public_key or '',
            recovery_public_key=recovery, started_at=now)
        device.is_active = False
        device.revoked_at = now
        device.removal_state = 'removal_pending'
        device.agent_allocation_active = True
        device.save(update_fields=['is_active', 'revoked_at', 'removal_state', 'agent_allocation_active'])
        AgentSession.objects.filter(device=device).update(status='expired', expires_at=now,
            fingerprint_challenge=None, fingerprint_challenge_expires=now)
        DeviceRemovalCode.objects.filter(device=device, used_at__isnull=True).update(invalidated_at=now)
    return {'operation_id': str(oid), **summary(device)}


def recovery_operation(request, payload):
    oid = operation_id(payload.get('operation_id'))
    operation = DeviceRemoval.objects.select_related('device__organization').filter(pk=oid).first()
    if not operation or payload.get('device_uuid') != operation.device.pc_id:
        raise RemovalError('OPERATION_NOT_FOUND', 404)
    verify(request, operation.recovery_public_key, operation.device.pc_id, f'removal:{oid}')
    return operation


def status(request, payload):
    operation = recovery_operation(request, payload)
    return {'operation_id': str(operation.pk), 'state': operation.state,
        'device_uuid': operation.device.pc_id, 'organization': operation.device.organization.name}


def complete(request, payload):
    operation = recovery_operation(request, payload)
    with transaction.atomic():
        operation = DeviceRemoval.objects.select_for_update().get(pk=operation.pk)
        if operation.state == 'removed':
            return {'operation_id': str(operation.pk), 'state': 'removed'}
        device = Device.objects.select_for_update().get(pk=operation.device_id)
        if (device.cert or '') != operation.old_certificate or device.removal_state != 'removal_pending':
            raise RemovalError('ENROLLMENT_CHANGED', 409)
        operation.state = 'removed'
        operation.completed_at = timezone.now()
        operation.save(update_fields=['state', 'completed_at'])
        device.removal_state = 'removed'
        device.agent_allocation_active = False
        device.save(update_fields=['removal_state', 'agent_allocation_active'])
    return {'operation_id': str(operation.pk), 'state': 'removed'}
