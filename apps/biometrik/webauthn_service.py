"""Server-issued WebAuthn ceremonies, authenticated registration capabilities."""
import base64
import json
import secrets
from datetime import timedelta
from urllib.parse import urlsplit
from django.conf import settings
from django.db import transaction, IntegrityError
from django.utils import timezone
from webauthn import verify_registration_response, verify_authentication_response
from webauthn.helpers.exceptions import WebAuthnException
from apps.common.models import BiometricFingerprint
from apps.agent.models import AgentSession
from .models import FingerprintSession


def b64(data): return base64.urlsafe_b64encode(data).decode().rstrip('=')


def rp():
    origin=settings.PUBLIC_SITE_URL.rstrip('/')
    address=urlsplit(origin)
    if not address.hostname or address.path or address.query or address.fragment:
        raise ValueError('PUBLIC_SITE_URL must be an origin')
    if address.scheme!='https' and not (address.scheme=='http' and address.hostname in ('localhost','127.0.0.1','::1')):
        raise ValueError('WebAuthn requires HTTPS or loopback')
    return address.hostname,origin


def credential(payload,registration=False):
    required=('rawId','clientDataJSON','attestationObject') if registration else ('rawId','clientDataJSON','authenticatorData','signature')
    if not isinstance(payload,dict) or any(not isinstance(payload.get(k),str) or not payload[k] or len(payload[k])>65536 for k in required):
        raise ValueError('Credential incomplete')
    raw=payload['rawId']
    response={'clientDataJSON':payload['clientDataJSON']}
    for name in required[2:]:response[name]=payload[name]
    return {'id':raw,'rawId':raw,'type':'public-key','response':response}


def register(session,payload):
    rp_id,origin=rp()
    if not session.challenge or session.status!='pending' or session.expires_at<=timezone.now() or not session.user.status or not session.user.organization.is_active:
        raise ValueError('Registration session invalid')
    result=verify_registration_response(credential=credential(payload,True),expected_challenge=bytes(session.challenge),
        expected_rp_id=rp_id,expected_origin=origin,require_user_verification=True)
    with transaction.atomic():
        if FingerprintSession.objects.filter(pk=session.pk,status='pending',challenge=session.challenge,expires_at__gt=timezone.now()).update(status='completed',challenge=None)!=1:
            raise ValueError('Registration already consumed')
        BiometricFingerprint.objects.create(user=session.user,source='phone',credential_id=result.credential_id,
            public_key=result.credential_public_key,sign_count=result.sign_count,rp_id=rp_id)


def options(session):
    rp_id,_=rp()
    fingerprint=BiometricFingerprint.objects.filter(user=session.user,rp_id=rp_id,public_key__isnull=False).first()
    if not fingerprint:raise ValueError('Verified WebAuthn credential missing; re-register legacy credentials')
    challenge=secrets.token_bytes(32)
    AgentSession.objects.filter(pk=session.pk,status='pending').update(fingerprint_challenge=challenge,
        fingerprint_challenge_expires=timezone.now()+timedelta(seconds=60))
    return {'challenge':b64(challenge),'credential_id':b64(bytes(fingerprint.credential_id)),'rp_id':rp_id}


def authenticate(session,payload):
    rp_id,origin=rp()
    if not session.fingerprint_challenge or not session.fingerprint_challenge_expires or session.fingerprint_challenge_expires<=timezone.now():
        raise ValueError('Challenge expired or absent')
    value=credential(payload)
    raw=base64.urlsafe_b64decode(value['rawId']+'='*(-len(value['rawId'])%4))
    with transaction.atomic():
        fp=BiometricFingerprint.objects.select_for_update().filter(user=session.user,rp_id=rp_id,credential_id=raw,public_key__isnull=False).first()
        if not fp:raise ValueError('Unknown credential')
        verified=verify_authentication_response(credential=value,expected_challenge=bytes(session.fingerprint_challenge),
            expected_rp_id=rp_id,expected_origin=origin,credential_public_key=bytes(fp.public_key),
            credential_current_sign_count=fp.sign_count,require_user_verification=True)
        if AgentSession.objects.filter(pk=session.pk,status='pending',fingerprint_challenge=session.fingerprint_challenge,
            fingerprint_challenge_expires__gt=timezone.now()).update(status='completed',fingerprint_challenge=None,fingerprint_challenge_expires=None)!=1:
            raise ValueError('Challenge already consumed')
        if BiometricFingerprint.objects.filter(pk=fp.pk,sign_count=fp.sign_count).update(sign_count=verified.new_sign_count)!=1:
            raise ValueError('Credential counter changed')
