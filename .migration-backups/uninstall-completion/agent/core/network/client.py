"""Central HTTPS client for the external BioGuard Backend.

The class preserves the deployed legacy endpoint shapes. Future challenge and
assertion methods only express the external API contract; they do not emulate a
backend when the endpoint is unavailable.
"""

import json
from collections.abc import Callable, Mapping
from typing import Any
import urllib.error
import urllib.request
from urllib.parse import urlparse

from .errors import (
    BackendAuthenticationError,
    BackendResponseError,
    BackendUnavailableError,
)


HeaderProvider = Callable[[], Mapping[str, str]]
Transport = Callable[[urllib.request.Request, float], bytes]


def _verified_urllib_transport(request: urllib.request.Request, timeout: float) -> bytes:
    """Use urllib's verified HTTPS defaults; no insecure SSL context is supplied."""
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


class BioGuardApiClient:
    """Owns external backend HTTP communication, timeouts, and typed failures."""

    def __init__(
        self,
        api_base: str,
        *,
        signed_headers_provider: HeaderProvider | None = None,
        transport: Transport | None = None,
        request_signer: Callable | None = None,
    ):
        self._api_base = api_base.rstrip("/")
        self._request_signer = request_signer
        self._signed_headers_provider = signed_headers_provider
        self._transport = transport or _verified_urllib_transport

    @property
    def api_base(self) -> str:
        return self._api_base

    def post(
        self,
        path: str,
        payload: Mapping[str, Any],
        *,
        timeout: float = 10,
        include_signed_headers: bool = True,
        request_signer: Callable | None = None,
    ) -> Any:
        body = json.dumps(dict(payload)).encode()
        return self._request(
            "POST",
            path,
            body=body,
            override_signer=request_signer,
            timeout=timeout,
            include_signed_headers=include_signed_headers,
        )

    def get(
        self,
        path: str,
        *,
        timeout: float = 6,
        include_signed_headers: bool = True,
    ) -> Any:
        return self._request(
            "GET",
            path,
            timeout=timeout,
            include_signed_headers=include_signed_headers,
        )

    def is_online(self) -> bool:
        try:
            self.get("/api/health/", timeout=3, include_signed_headers=False)
            return True
        except (BackendUnavailableError, BackendResponseError):
            return False

    # Existing deployed backend contracts -------------------------------------------------

    def start_session(self, username: str, device_id: str) -> dict[str, Any]:
        return self.post("/api/agent/session/start/", {
            "username": username,
            "pc_id": device_id,
        })

    def check_face(
        self,
        *,
        session_id: str | None,
        username: str,
        device_id: str,
        image: str,
    ) -> dict[str, Any]:
        return self.post("/api/face/agent/check/", {
            "session_id": session_id,
            "username": username,
            "pc_id": device_id,
            "image": image,
        })

    def get_remote_approval_status(self, approval_type: str, session_id: str) -> Any:
        paths = {
            "face": f"/api/agent/face/phone/status/{session_id}/",
            "fingerprint": f"/api/agent/fingerprint/phone/status/{session_id}/",
        }
        try:
            path = paths[approval_type]
        except KeyError as error:
            raise ValueError(f"Unsupported remote approval type: {approval_type}") from error
        return self.get(path)

    def get_device_status(self, device_id: str, username: str) -> Any:
        return self.get(
            f"/api/agent/device/status/?pc_id={device_id}&username={username}"
        )

    # Future backend contracts -------------------------------------------------------------

    def get_auth_challenge(
        self,
        *,
        device_id: str,
        requested_provider_ids: list[str],
        session_context: str,
    ) -> dict[str, Any]:
        return self.post("/api/auth/challenge", {
            "device_id": device_id,
            "requested_provider_ids": requested_provider_ids,
            "session_context": session_context,
        })

    def submit_auth_assertion(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.post("/api/auth/assertions", payload)

    def fetch_offline_policy(self, device_id: str) -> Any:
        return self.get(f"/api/agent/offline-policy?device_id={device_id}")

    def send_events(self, events: list[Mapping[str, Any]]) -> dict[str, Any]:
        return self.post("/api/agent/audit-events/batch", {"events": events})

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        timeout: float,
        include_signed_headers: bool,
        override_signer: Callable | None = None,
    ) -> Any:
        headers = self._headers(method, include_signed_headers)
        signer = override_signer or (self._request_signer if include_signed_headers else None)
        if signer:
            from urllib.parse import urlsplit
            target = urlsplit(self._url_for(path))
            try:
                headers.update(signer(method, target.path + ('?' + target.query if target.query else ''), body or b''))
            except Exception as error:
                raise BackendAuthenticationError('Device request signing failed') from error
        request = urllib.request.Request(
            self._url_for(path),
            data=body,
            headers=headers,
            method=method,
        )
        try:
            raw = self._transport(request, timeout)
        except urllib.error.HTTPError as error:
            try:
                response_body = error.read().decode(errors="replace")
            except OSError:
                response_body = None
            raise BackendResponseError(
                f"Backend returned HTTP {error.code}",
                status_code=error.code,
                response_body=response_body,
            ) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise BackendUnavailableError("BioGuard Backend is unavailable") from error

        try:
            if raw.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                raise BackendResponseError("Backend returned an HTML page instead of an API response")
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            try:
                return raw.decode().strip()
            except UnicodeDecodeError as error:
                raise BackendResponseError("Backend returned a non-text response") from error

    def _headers(self, method: str, include_signed_headers: bool) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        hostname = urlparse(self._api_base).hostname or ""
        if hostname.endswith((".ngrok-free.dev", ".ngrok-free.app", ".ngrok.io", ".ngrok.app")):
            headers["ngrok-skip-browser-warning"] = "true"
        if method == "POST":
            headers["Content-Type"] = "application/json"
        if not include_signed_headers or self._signed_headers_provider is None:
            return headers
        try:
            headers.update(dict(self._signed_headers_provider()))
        except Exception as error:
            raise BackendAuthenticationError(
                "Could not generate device authentication headers"
            ) from error
        return headers

    def _url_for(self, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError("Backend API paths must begin with '/'")
        return f"{self._api_base}{path}"
