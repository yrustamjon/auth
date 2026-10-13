"""Online-only removal orchestration, independent of Windows and UI code."""
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from core.network.signatures import sign_headers
from core.network.errors import BackendResponseError


def recovery_keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()).decode()
    public = key.public_key().public_bytes(serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return private, public


class RemovalController:
    def __init__(self, client, device_uuid, receipts, cleanup):
        self.client, self.device_uuid = client, device_uuid
        self.receipts, self.cleanup = receipts, cleanup
        self.draft = None

    def _draft(self):
        if self.draft is None:
            private, public = recovery_keypair()
            self.draft = {'version': 1, 'operation_id': str(uuid.uuid4()),
                'device_uuid': self.device_uuid, 'private_key': private, 'public_key': public,
                'local_cleanup_done': False}
        return self.draft

    def _receipt(self):
        receipt = self.receipts.load()
        if not receipt or receipt.get('version') != 1 or receipt.get('device_uuid') != self.device_uuid:
            raise ValueError('Matching protected removal receipt required')
        return receipt

    def _post(self, action, data, receipt, *, recovery=False):
        certificate = 'removal:' + receipt['operation_id'] if recovery else 'removal-bootstrap'
        signer = lambda method, target, body: sign_headers(receipt['private_key'].encode(),
            method, target, body, self.device_uuid, certificate)
        return self.client.post('/api/agent/removal/' + action + '/',
            {'device_uuid': self.device_uuid, **data}, timeout=10, request_signer=signer)

    def check(self, code):
        receipt = self._draft()
        return self._post('check', {'code': code.strip(), 'recovery_public_key': receipt['public_key']}, receipt)

    def begin(self, code):
        existing = self.receipts.load()
        if existing:
            # A receipt may survive a lost response or a later reinstallation.
            # Resolve its server state before reusing or replacing its key.
            try:
                result = self.resume()
            except BackendResponseError as error:
                if error.status_code != 404:
                    raise
            else:
                state = result.get('state')
                if state == 'removal_pending':
                    return result
                if state != 'removed':
                    raise ValueError('Unexpected removal state')
                self.draft = None
                existing = None
        receipt = existing or self._draft()
        if receipt.get('device_uuid') != self.device_uuid:
            raise ValueError('Receipt belongs to a different device')
        # Persist before any server state change, so a lost response is recoverable.
        self.receipts.save(receipt)
        return self._post('begin', {'code': code.strip(), 'operation_id': receipt['operation_id'],
            'recovery_public_key': receipt['public_key']}, receipt)

    def resume(self):
        receipt = self._receipt()
        return self._post('status', {'operation_id': receipt['operation_id']}, receipt, recovery=True)

    def cleanup_and_complete(self):
        receipt = self._receipt()
        state = self.resume().get('state')  # No destructive work when offline.
        if state == 'removed':
            self.receipts.clear()
            return {'state': 'removed'}
        if state != 'removal_pending':
            raise ValueError('Backend has not approved removal')
        if not receipt.get('local_cleanup_done'):
            self.cleanup()
            receipt['local_cleanup_done'] = True
            self.receipts.save(receipt)
        result = self._post('complete', {'operation_id': receipt['operation_id']}, receipt, recovery=True)
        if result.get('state') != 'removed':
            raise ValueError('Removal completion was not acknowledged')
        self.receipts.clear()
        return result
