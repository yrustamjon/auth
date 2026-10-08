"""Authenticated device requests with shared-database, bounded replay records."""
import base64
import json
import re
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from django.db import IntegrityError, OperationalError, transaction
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from apps.common.models import Device, Users
from .models import RequestNonce, AgentSession
from .signatures import envelope


class AuthenticationFailure(ValueError):
    def __init__(self, status=401):
        self.status = status


def consume_nonce(certificate, nonce, expires_at):
    try:
        with transaction.atomic():
            RequestNonce.objects.filter(expires_at__lt=timezone.now()).delete()
            RequestNonce.objects.create(certificate_id=certificate, nonce=nonce, expires_at=expires_at)
        return True
    except IntegrityError:
        return False
    except OperationalError as error:
        # A busy SQLite writer is denied, never accepted without replay protection.
        if 'locked' in str(error).lower():
            return False
        raise


def verify_signature(request, public_pem, device, certificate):
    headers=request.headers
    stamp=headers.get('X-Timestamp','')
    nonce=headers.get('X-Nonce','')
    if (headers.get('X-BioGuard-Version') != '1' or headers.get('X-PC-ID') != device or
        headers.get('X-Cert-ID') != certificate or not re.fullmatch(r'[0-9]{1,12}',stamp) or
        not re.fullmatch(r'[a-f0-9]{32,128}',nonce)):
        raise AuthenticationFailure()
    value=int(stamp)
    now=int(time.time())
    if value < now-300 or value > now+30:
        raise AuthenticationFailure()
    try:
        key=serialization.load_pem_public_key(public_pem.encode())
        if not isinstance(key,rsa.RSAPublicKey) or key.key_size < 2048:
            raise ValueError('Invalid public key')
        encoded=headers.get('X-Signature','')
        if len(encoded)>2048:
            raise ValueError('Signature too large')
        signature=base64.b64decode(encoded,validate=True)
        key.verify(signature,envelope(request.method,request.get_full_path(),request.body,device,certificate,stamp,nonce),
                   padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=32),hashes.SHA256())
    except (ValueError, TypeError, InvalidSignature, UnsupportedAlgorithm):
        raise AuthenticationFailure() from None
    return nonce, datetime.fromtimestamp(value+301,tz=dt_timezone.utc)


def verify_bootstrap(request, payload):
    verify_signature(request, payload['public_key'], payload['device_uuid'], 'bootstrap')
    # The organization token is claimed atomically by enrollment; bootstrap has
    # no previously enrolled certificate and cannot authorize any desktop route.


class DeviceSignatureMiddleware:
    def __init__(self,get_response):
        self.get_response=get_response

    def __call__(self,request):
        desktop=(request.path.startswith('/api/agent/') or request.path == '/api/face/agent/check/')
        bootstrap=request.path == '/api/agent/activate/'
        phone='/phone/submit/' in request.path
        if bootstrap:
            _ = request.body  # Cache exact bytes before DRF parses its data stream.
        if desktop and not bootstrap and not phone:
            try:
                certificate=request.headers.get('X-Cert-ID','')
                device=Device.objects.select_related('organization').filter(cert=certificate).first() if certificate else None
                if device is None or not device.device_public_key:
                    raise AuthenticationFailure()
                nonce,expiry=verify_signature(request,device.device_public_key,device.pc_id,device.cert)
                if (device.revoked_at or not device.is_active or not device.organization.is_active or
                    device.enrollment_status != Device.EnrollmentStatus.AGENT_ENROLLED):
                    raise AuthenticationFailure(403)
                if request.method == 'GET':
                    payload=request.GET
                else:
                    try: payload=json.loads(request.body or b'{}')
                    except (ValueError,UnicodeError): raise AuthenticationFailure(400)
                if not isinstance(payload,dict) and request.method != 'GET':
                    raise AuthenticationFailure(400)
                for name in ('pc_id','device_id','device_uuid'):
                    if name in payload and payload[name] != device.pc_id:
                        raise AuthenticationFailure(403)
                username=payload.get('username')
                if username is not None and not Users.objects.filter(organization=device.organization,username=username,status=True).exists():
                    raise AuthenticationFailure(403)
                session_id=payload.get('session_id')
                if '/phone/status/' in request.path:
                    session_id=request.path.rstrip('/').split('/')[-1]
                if session_id:
                    try: session=AgentSession.objects.select_related('user').get(session_id=session_id,device=device)
                    except (AgentSession.DoesNotExist,ValueError,ValidationError): raise AuthenticationFailure(403)
                    if not session.user.status or (username is not None and username != session.user.username):
                        raise AuthenticationFailure(403)
                if not consume_nonce(certificate,nonce,expiry):
                    raise AuthenticationFailure(409)
                request.bioguard_device=device
            except AuthenticationFailure as error:
                return JsonResponse({'detail':'Device request rejected'},status=error.status)
            except OperationalError:
                return JsonResponse({'detail':'Authentication database unavailable'},status=503)
        return self.get_response(request)
