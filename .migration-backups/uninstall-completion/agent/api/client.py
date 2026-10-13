"""Backward-compatible HTTP helpers for the external BioGuard Backend.

New code should receive ``core.network.BioGuardApiClient`` explicitly. These
functions retain the public behavior used by the existing Windows UI while
delegating all transport work to that client.
"""

import logging
from typing import Any

from core.config import API_BASE, DEVICE_UUID
from core.network.client import BioGuardApiClient


LOGGER = logging.getLogger(__name__)


def _sign_device_request(method, target, body):
    from core.cert import load_cert, _load_private_key_bytes
    from core.network.signatures import sign_headers
    cert = load_cert()
    key = _load_private_key_bytes()
    if not cert or not key or cert.get('pc_id') != DEVICE_UUID:
        raise ValueError('Protected device credentials are required')
    return sign_headers(key, method, target, body, DEVICE_UUID, cert['cert_id'])


def get_default_client() -> BioGuardApiClient:
    """Construct the compatibility client using the configured backend URL."""
    return BioGuardApiClient(API_BASE, request_signer=_sign_device_request)


def api_post(path: str, payload: dict) -> dict:
    """Compatibility wrapper retaining the old function name and arguments."""
    return get_default_client().post(path, payload)


def api_get(path: str) -> Any:
    """Compatibility wrapper retaining JSON-or-text response behavior."""
    return get_default_client().get(path)


def is_online() -> bool:
    """Return whether the configured backend health endpoint is reachable."""
    return get_default_client().is_online()
