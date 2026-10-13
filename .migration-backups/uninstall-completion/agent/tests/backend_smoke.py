"""Real HTTP integration against a disposable local Django database.

Run with both repositories on PYTHONPATH, DJANGO_SETTINGS_MODULE set to isolated
local settings, migrations applied, and Django listening at 127.0.0.1:8000.
Creates only uniquely named synthetic records and removes them in finally.
Never use a production database/backend. No private keys or tokens are written.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    import django
    django.setup()
    from django.conf import settings
    from apps.common.models import Organization,Device,Users
    from apps.org.models import OrgToken
    from core.network.client import BioGuardApiClient, _verified_urllib_transport
    from core.network.errors import BackendResponseError
    from core.network.signatures import sign_headers
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import urllib.error
    import uuid
    assert settings.DATABASES['default']['ENGINE']=='django.db.backends.sqlite3'
    assert str(settings.DATABASES['default']['NAME']).startswith('/workspace/.local/bioguard/'), 'Disposable cloud database required'
    tag='signed-smoke-'+uuid.uuid4().hex
    org=Organization.objects.create(name='Synthetic smoke',slug=tag)
    try:
        user=Users.objects.create(organization=org,username=tag,fio='Synthetic',lavozim='Test')
        device=Device.objects.create(organization=org,pc_id=tag,license='UNKNOWN',location='Test',is_active=False,enrollment_status=Device.EnrollmentStatus.BROWSER_APPROVED)
        token=OrgToken.objects.create(org=org)
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
        public=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        base='http://127.0.0.1:8000'
        raw=BioGuardApiClient(base)
        assert raw.is_online()
        try: raw.start_session(tag,tag)
        except BackendResponseError as error: assert error.status_code==401
        else: raise AssertionError('Unsigned request accepted')
        result=raw.post('/api/agent/activate/',dict(activation_code=token.token,device_uuid=tag,windows_license='SYNTHETIC',public_key=public),request_signer=lambda method,target,body:sign_headers(private,method,target,body,tag,'bootstrap'))
        certificate=result['certificate']['cert_id']
        captured=[]
        def transport(request,timeout):
            captured.append(request)
            return _verified_urllib_transport(request,timeout)
        client=BioGuardApiClient(base,request_signer=lambda method,target,body:sign_headers(private,method,target,body,tag,certificate),transport=transport)
        assert client.post('/api/agent/check-pc/',dict(device_uuid=tag,windows_license='SYNTHETIC'))['ok']
        session=client.start_session(tag,tag)
        replay=captured[-1]
        try: _verified_urllib_transport(replay,3)
        except urllib.error.HTTPError as error: assert error.code==409
        else: raise AssertionError('Replay accepted')
        for method in ('face','fingerprint'):
            assert client.get_remote_approval_status(method,session['session_id'])=='pending'
        assert client.get_device_status(tag,tag)['status']=='active'
        assert client.check_face(session_id=session['session_id'],username=tag,device_id=tag,image='synthetic')['status']=='failed'
        device.refresh_from_db();device.revoked_at=django.utils.timezone.now();device.save()
        try: client.get_device_status(tag,tag)
        except BackendResponseError as error: assert error.status_code==403
        else: raise AssertionError('Revoked certificate accepted')
        print('PASS: real HTTP enrollment -> signed check-pc -> session -> both polls -> missing-face rejection -> replay and revocation rejection')
    finally:
        org.delete()


if __name__=='__main__':main()
