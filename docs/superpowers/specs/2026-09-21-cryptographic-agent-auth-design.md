# Cryptographic Agent Authentication Design

## Goal

Add an additive, server-authoritative authentication foundation for Windows Hello, FIDO2, passkeys, and future platform providers. The foundation must cryptographically authenticate the Agent device, perform genuine WebAuthn registration and assertion ceremonies, enforce user/device/credential/policy state, create auditable decisions, and preserve every existing Agent route unchanged.

## Scope and compatibility

This design adds a new Django app, `apps.authentication`, and routes below `/api/agent/auth/`. It does not change the request handling, response format, or authorization requirements of any existing route, including:

- `/api/agent/session/start/`
- `/api/face/agent/check/`
- `/api/agent/face/phone/status/<session_id>/`
- `/api/agent/fingerprint/phone/status/<session_id>/`
- `/api/agent/device/status/`
- `/api/agent/activate/`
- `/api/agent/validate-code/`
- `/api/agent/check-pc/`
- `/api/health/`

The source currently has no `/api/agent/activate/personal/` route. This work will not create or remove it; deployment owners should retain any environment-specific route separately.

The legacy phone fingerprint flow remains a **legacy remote approval** flow. Its current server code only matches a returned credential ID and does not verify an assertion, so it must not be represented as WebAuthn, FIDO2, hardware-backed, or cryptographically verified.

## Existing-system facts that constrain the design

`apps.common.models.Users.status` is the employee-user activation state. `apps.common.models.Device` owns `pc_id`, opaque `cert`, `device_public_key`, and `is_active`. Agent routes are currently anonymous and do not validate a device request signature. Activation writes the public key and certificate lookup value, but the certificate is not proof of possession.

The new routes must therefore require a new device-signed envelope. The old routes cannot be upgraded in place because deployed Agents depend on their existing contracts.

## Components

### New `apps.authentication` app

The app owns the new data models, WebAuthn/service functions, signed-device-request authentication, API views, URL routes, and focused Django tests. It depends on the existing `Users`, `Device`, and `Organization` models but does not alter their business behavior.

### Data models

`AuthenticationCredential`

- UUID primary identifier, `user`, and `device` foreign keys.
- `provider`: `windows_hello`, `fido2`, `passkey`, or `future_platform_provider`.
- Globally unique binary WebAuthn `credential_id`, binary COSE `credential_public_key`, and non-negative `sign_count`.
- `credential_device_type`, `credential_backed_up`, and bounded JSON `metadata` for verified public authenticator properties.
- `created_at`, `last_used_at`, `revoked_at`, and `is_active`.
- No private key, biometric template, PIN, password, raw assertion, or raw registration attestation is retained.

`AuthenticationChallenge`

- UUID `challenge_id`, `user`, `device`, `provider`, and purpose enum: `webauthn_registration`, `webauthn_authentication`, or `offline_policy_refresh`.
- SHA-256 hash of a 32-byte `secrets.token_bytes()` challenge; `created_at`, `expires_at`, `consumed_at`, and non-sensitive JSON `metadata`.
- The raw challenge is returned exactly once in WebAuthn options and is not stored. At completion, the server decodes the challenge from signed `clientDataJSON`, hashes it, compares it in constant time with the stored hash, and passes that exact byte value to the maintained WebAuthn library for independent ceremony verification. This preserves library verification while avoiding raw-challenge-at-rest storage.

`DeviceRequestNonce`

- Links a device to the SHA-256 hash of its signed-request nonce and an expiry time.
- Has a database uniqueness constraint on `(device, nonce_hash)`. It is distinct from `AuthenticationChallenge` and never used as a WebAuthn challenge.

`AuthenticationPolicy`

- One active policy per organization; JSON `allowed_providers` and `provider_priority`.
- `minimum_auth_strength` (`user_presence` or `user_verification`), `offline_auth_enabled`, `offline_max_hours`, `session_timeout_seconds`, and `reauthentication_interval_seconds`.
- Policy defaults to cryptographic providers with `user_verification`; it is selected only on the server. The Agent cannot lower it.

`AuthenticationAuditEvent`

- Nullable user/device/credential relations so even unknown-device failures can be recorded.
- Event type, boolean result, normalized reason code, provider, timestamp, and non-sensitive JSON metadata.
- Required events include challenge creation, success, failure, replay rejection, credential registration, credential revocation, device rejection/revocation, and offline policy success/failure.
- Required reason codes include `SUCCESS`, `INVALID_ASSERTION`, `EXPIRED_CHALLENGE`, `REPLAYED_CHALLENGE`, `DEVICE_DISABLED`, `USER_DISABLED`, `CREDENTIAL_REVOKED`, `POLICY_REJECTED`, `INVALID_DEVICE_SIGNATURE`, and `REUSED_REQUEST_NONCE`.

`Device` receives an additive `revoked_at` timestamp. A revoked device is inactive for new cryptographic authentication and all credentials bound to it are rejected. Existing `is_active` behavior remains unchanged.

### Signed device-request envelope

Every new `/api/agent/auth/` request authenticates the device before any client-supplied user or device IDs are used. It requires:

- `X-BioGuard-Device-ID`: registered `Device.pc_id` identifier.
- `X-Cert-ID`: registered certificate lookup value only.
- `X-BioGuard-Timestamp`: UTC Unix seconds within the configured five-minute acceptance window.
- `X-BioGuard-Nonce`: base64url random value of at least 16 bytes.
- `X-BioGuard-Signature`: base64url signature made by the private key corresponding to `Device.device_public_key`.

The exact canonical UTF-8 payload is:

```text
BIOGUARD-AGENT-REQUEST-V1\n
HTTP_METHOD\n
REQUEST_PATH\n
BODY_SHA256_HEX\n
TIMESTAMP\n
NONCE\n
DEVICE_ID\n
```

`HTTP_METHOD` is uppercase; `REQUEST_PATH` is the path only, including its leading and trailing slash; `BODY_SHA256_HEX` is the lowercase SHA-256 digest of the exact received bytes; `TIMESTAMP`, `NONCE`, and `DEVICE_ID` are the exact validated header values. The delimiters and version prefix make field boundaries unambiguous.

The initial supported public-key encoding is PEM SubjectPublicKeyInfo. RSA keys use RSA-PSS/SHA-256 and EC keys use ECDSA/SHA-256; Ed25519 keys use Ed25519. The key type determines verification, so an untrusted algorithm header cannot weaken verification. A stored public key in another legacy format must be re-enrolled or migrated explicitly; the opaque certificate never provides a fallback proof.

Within one database transaction the service locks the device, verifies device/org state, timestamp, association, key signature, and writes the nonce hash. The database constraint converts a concurrent duplicate into `REUSED_REQUEST_NONCE`. Invalid signatures never acquire a valid nonce. Expired nonce records may be cleaned up after their timestamp window.

### WebAuthn configuration and dependency

The project receives explicit settings:

- `WEBAUTHN_RP_ID`
- `WEBAUTHN_RP_NAME`
- `WEBAUTHN_EXPECTED_ORIGIN`
- `DEVICE_REQUEST_SIGNATURE_MAX_AGE_SECONDS`

They are static deployment configuration, never inferred from `Host`, forwarded headers, or Agent input. Development defaults are explicit localhost values; production must override them through deployment configuration.

The implementation pins `webauthn==2.8.0`, the maintained Duo Labs package installed with `pip install webauthn`. The project uses Python 3.13 and Django 6.0.2. `webauthn` 2.8.0 supports Python >=3.10 and requires `cryptography>=46.0.0`; the repository already pins `cryptography==46.0.5`. It adds compatible `cbor2`, `pyasn1`, `pyasn1-modules`, and `pyOpenSSL` transitive requirements. `webauthn` 3.0.0 requires `cryptography>=49.0.0`, so it is deliberately not selected until this repository upgrades its pinned cryptography version.

The maintained library functions `generate_registration_options`, `verify_registration_response`, `generate_authentication_options`, and `verify_authentication_response` perform the WebAuthn ceremony. The backend does not implement WebAuthn cryptographic parsing or signature verification itself.

### Registration lifecycle

1. A device-signed `POST /api/agent/auth/credentials/register/options/` supplies only a requested provider and a user identifier.
2. The server resolves the active user inside the signed device's organization, enforces policy, creates a purpose-bound registration challenge, and returns JSON-compatible `PublicKeyCredentialCreationOptions` plus `challenge_id` and expiry.
3. The Agent invokes Windows `WebAuthNAuthenticatorMakeCredential` or another platform authenticator and converts the browser-equivalent WebAuthn result to base64url JSON.
4. A separately signed `POST /api/agent/auth/credentials/register/complete/` submits `challenge_id`, provider, and the response.
5. In a locked transaction, the server validates user/device/provider/purpose/expiry/unused state, the library verifies the registration response using configured RP ID/origin, then the server stores only verified credential material. It marks the challenge consumed after verification and audits `CREDENTIAL_REGISTERED`.

Arbitrary credential IDs, public keys, and attestation data are never accepted outside this verified ceremony.

### Authentication lifecycle

1. A device-signed `POST /api/agent/auth/challenge/` requests an authentication challenge for an active user/provider.
2. The server validates device/user/policy, creates a purpose-bound authentication challenge, calls `generate_authentication_options`, and returns `challenge_id`, expiry, allowed providers, and JSON-compatible options restricted to active credentials on that device.
3. The Agent uses Windows `WebAuthNAuthenticatorGetAssertion` or a future platform API and submits JSON-compatible assertion data through a separately signed `POST /api/agent/auth/assertion/verify/`.
4. In one locked transaction, the server revalidates user/device/credential/policy ownership and status, verifies challenge hash/purpose/expiry/unused state, then calls `verify_authentication_response` with the stored public key, stored counter, expected RP ID, expected origin, and recovered expected challenge.
5. Only a valid library result consumes the challenge. The returned signature counter updates the stored counter according to the library result; a zero counter is not independently treated as compromise. Success updates `last_used_at` and emits `AUTH_SUCCESS`; failures emit `AUTH_FAILED` or `AUTH_REPLAY_REJECTED` with a normalized reason.

The response never trusts `authenticated: true` or any client-declared success flag.

### Revocation and policy semantics

- A credential with `revoked_at` or `is_active=False` cannot register an assertion; other credentials and devices remain usable.
- A device with `is_active=False` or `revoked_at` rejects all of its credentials; devices elsewhere remain unaffected.
- A user with `status=False` rejects all cryptographic authentication regardless of device or credential.
- A provider omitted from `allowed_providers`, or an assertion that does not satisfy required user verification, is rejected with `POLICY_REJECTED`.

The model service exposes explicit credential and device revocation operations for server administration. Agent-facing enrollment/authentication routes do not grant the Agent authority to revoke identities.

### Offline policy contract

`POST /api/agent/auth/offline-policy/` is device-signed and returns a signed policy only when dedicated server signing configuration exists. It never returns an unsigned replacement.

The signer uses a dedicated Ed25519 server private key, loaded from deployment-managed `OFFLINE_POLICY_SIGNING_PRIVATE_KEY_PEM`, with a configured `OFFLINE_POLICY_SIGNING_KEY_ID`. It never uses a device key or the repository's Fernet key. The response contains a versioned policy payload and a detached base64url Ed25519 signature over the documented canonical UTF-8 JSON serialization. The Agent verifies against a public key provisioned independently of this response; it must reject any key introduced by the response itself.

Private-key storage, production key rotation, and trusted public-key distribution are deployment responsibilities not present in this repository. The endpoint remains unavailable (`503`) if the dedicated key is absent. The contract documents key IDs, a two-key overlap rotation process, and the need to ship trust anchors with the Agent installer or an equally trusted update channel.

## Error handling and audit behavior

New routes use structured JSON errors with a stable `code`; no raw exception, raw challenge, full assertion, PIN, password, biometric template, or private key appears in responses or audit metadata. Device-envelope errors are rejected before ceremony processing. Unknown/replayed/expired challenges return an error and write audit entries where a safely known context exists. A failed assertion does not consume its challenge; a successful assertion consumes it atomically.

## Testing strategy

Django tests cover secure 32-byte challenge creation, expiry, unknown challenge, wrong purpose, wrong user/device, device/user/credential revocation, policy rejection, duplicate and concurrent challenge consumption, invalid request signatures, stale/reused request nonces, wrong certificate/device associations, wrong RP ID/origin, invalid assertions, verified registration, verified authentication, counter updates, offline signer absence/signature behavior, and legacy route response compatibility.

Test fixtures use genuine valid WebAuthn ceremony data from the selected library where practical. Unit tests may isolate the library boundary only to test server state and error mapping; they do not replace end-to-end verifier coverage.

## Delivery status boundaries

Implemented by this work: data architecture, device request proof, real WebAuthn registration/assertion verification, policy enforcement, replay protection, revocation checks, audit records, signed-offline-policy contract/implementation when a configured signing key is supplied, tests, and Agent contract documentation.

Partially implemented by this work: offline policy production operations. The cryptographic contract exists, but production KMS/HSM storage, installer trust-anchor provisioning, and coordinated key rotation are deployment work.

Not implemented by this work: desktop Agent code, Windows Hello UI/API calls, macOS native integration, legacy face/phone-flow redesign, migration of legacy endpoints to device signatures, and support for non-PEM legacy device key formats.
