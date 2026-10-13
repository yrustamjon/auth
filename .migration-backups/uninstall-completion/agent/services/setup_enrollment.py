"""Pre-copy enrollment journal: preserve key before a token-consuming request."""
from core.network.errors import BackendResponseError
from core.network.signatures import sign_headers
from services.removal import recovery_keypair


class SetupEnrollment:
    def __init__(self, device_uuid, store, client, activate, save_cert):
        self.device_uuid, self.store, self.client = device_uuid, store, client
        self.activate_request, self.save_cert = activate, save_cert

    def recover(self):
        prepared = self.store.load()
        if not prepared:
            return False
        if prepared.get('device_uuid') != self.device_uuid:
            raise ValueError('Prepared enrollment belongs to a different device')
        signer = lambda method, target, body: sign_headers(prepared['private_key'].encode(),
            method, target, body, self.device_uuid, 'bootstrap')
        try:
            result = self.client.post('/api/agent/activate/status/',
                {'device_uuid': self.device_uuid, 'public_key': prepared['public_key']},
                timeout=10, request_signer=signer)
        except BackendResponseError as error:
            if error.status_code == 404:
                return False
            raise
        certificate = result.get('certificate')
        if not isinstance(certificate, dict) or certificate.get('pc_id') != self.device_uuid or not certificate.get('cert_id'):
            raise ValueError('Invalid recovered enrollment')
        self.save_cert(certificate, prepared['private_key'])
        self.store.clear()
        return True

    def activate(self, token):
        prepared = self.store.load()
        if prepared is not None:
            if self.recover():
                return {'status': 'recovered'}
        else:
            private, public = recovery_keypair()
            prepared = {'version': 1, 'device_uuid': self.device_uuid,
                'private_key': private, 'public_key': public}
            self.store.save(prepared)
        result = self.activate_request(token, keypair=(prepared['public_key'], prepared['private_key']))
        self.store.clear()  # activate_org persists the accepted certificate first.
        return result
