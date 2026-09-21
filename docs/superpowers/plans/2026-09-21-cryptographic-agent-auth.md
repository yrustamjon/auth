# Cryptographic Agent Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an additive, cryptographically verified Agent-device and WebAuthn authentication subsystem without changing legacy Agent APIs.

**Architecture:** A new `apps.authentication` app owns server-side policy, credential, challenge, request-nonce, and audit records. The four new WebAuthn routes require device proof first, then use `webauthn==2.8.0` for genuine ceremonies under database locks.

**Tech Stack:** Django 6.0.2, DRF, Python 3.13, `cryptography==46.0.5`, Duo Labs `webauthn==2.8.0`.

**Spec:** `docs/superpowers/specs/2026-09-21-cryptographic-agent-auth-design.md`

## Global Constraints

- Preserve every current legacy Agent, face, phone, activation, device-status, and health endpoint.
- New API paths are under `/api/agent/auth/` and require signed device proof; an opaque certificate is lookup-only.
- Canonical device input is UTF-8 `BIOGUARD-AGENT-REQUEST-V1\\n{METHOD}\\n{PATH}\\n{BODY_SHA256_HEX}\\n{TIMESTAMP}\\n{NONCE}\\n{DEVICE_ID}\\n`.
- Request nonce and 32-byte WebAuthn challenge are separate and stored independently as SHA-256 hashes.
- RP ID, RP name, and expected origin are explicit settings, never request-derived.
- WebAuthn response validation is exclusively delegated to `webauthn`; no custom WebAuthn signature parsing is written.
- Do not persist private keys, PINs, passwords, templates, raw assertions, or raw attestation.
- Only a successful assertion consumes a challenge, inside the transaction that verifies it.
- An offline policy is unsigned never; a signing-key failure is fail-closed.

## Review Focus

- Missing or malformed signed headers return stable non-secret errors; Task 3 has this test.
- A concurrent replay leaves one success and one replay error; Tasks 3 and 6 have unique-constraint tests.
- Unsupported but parseable PEM keys fail closed; Task 3 tests this.
- Bad base64url/client data never exposes parsing exceptions; Tasks 4-6 test it.
- Missing offline signing material returns no policy fields; Task 7 tests it.

---

### Task 1: Create app scaffolding and explicit configuration

**Files:**

- Create: `apps/authentication/__init__.py`
- Create: `apps/authentication/apps.py`
- Create: `apps/authentication/urls.py`
- Create: `apps/authentication/tests/__init__.py`
- Create: `apps/authentication/tests/test_settings.py`
- Modify: `project/settings.py`
- Modify: `project/urls.py`
- Modify: `req.text`

**Interfaces:**

- Produces app label `authentication` and empty URL list ready for later routes.
- Produces explicit `WEBAUTHN_RP_ID`, `WEBAUTHN_RP_NAME`, `WEBAUTHN_EXPECTED_ORIGIN`, and `DEVICE_REQUEST_SIGNATURE_MAX_AGE_SECONDS`.

- [ ] **Step 1: Write the failing settings test**

```python
from django.conf import settings
from django.test import SimpleTestCase


class WebAuthnSettingsTests(SimpleTestCase):
    def test_explicit_non_host_derived_configuration(self):
        self.assertEqual(settings.WEBAUTHN_RP_ID, "localhost")
        self.assertEqual(settings.WEBAUTHN_RP_NAME, "AD BioGuard")
        self.assertEqual(settings.WEBAUTHN_EXPECTED_ORIGIN, "http://localhost:8000")
        self.assertEqual(settings.DEVICE_REQUEST_SIGNATURE_MAX_AGE_SECONDS, 300)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_settings -v 2`

Expected: FAIL because the app and settings are absent. Install existing pinned runtime packages plus `webauthn==2.8.0` only if the checked-in virtual environment prevents Django bootstrap; do not change production Celery behavior.

- [ ] **Step 3: Add the minimum configuration**

```python
# project/settings.py
WEBAUTHN_RP_ID = os.environ.get("WEBAUTHN_RP_ID", "localhost")
WEBAUTHN_RP_NAME = os.environ.get("WEBAUTHN_RP_NAME", "AD BioGuard")
WEBAUTHN_EXPECTED_ORIGIN = os.environ.get(
    "WEBAUTHN_EXPECTED_ORIGIN", "http://localhost:8000"
)
DEVICE_REQUEST_SIGNATURE_MAX_AGE_SECONDS = int(
    os.environ.get("DEVICE_REQUEST_SIGNATURE_MAX_AGE_SECONDS", "300")
)
```

Add the app to `INSTALLED_APPS`, add its root URL include after legacy includes, and append `webauthn==2.8.0` to `req.text`.

- [ ] **Step 4: Verify configuration**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_settings -v 2 && PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py check`

Expected: PASS.

### Task 2: Add authentication state, policy, audit, and revocation models

**Files:**

- Create: `apps/authentication/models.py`
- Create: `apps/authentication/services/__init__.py`
- Create: `apps/authentication/services/audit.py`
- Create: `apps/authentication/services/policy.py`
- Create: `apps/authentication/services/revocation.py`
- Create: `apps/authentication/migrations/0001_initial.py`
- Create: `apps/authentication/tests/factories.py`
- Create: `apps/authentication/tests/test_models.py`
- Modify: `apps/common/models.py`
- Create: `apps/common/migrations/0009_device_revoked_at.py`

**Interfaces:**

- Produces `AuthenticationCredential.revoke()`, `AuthenticationChallenge`, `DeviceRequestNonce`, `AuthenticationPolicy.for_organization()`, `record_authentication_event()`, and `revoke_device()`.

- [ ] **Step 1: Write failing ownership/revocation/policy tests**

```python
class StateTests(TestCase):
    def test_credential_revocation_is_independent(self):
        first = credential_factory(device=self.device_a)
        second = credential_factory(device=self.device_b)
        first.revoke()
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertIsNotNone(first.revoked_at)
        self.assertTrue(second.is_active)

    def test_device_revocation_does_not_disable_another_device(self):
        revoke_device(self.device_a)
        self.device_a.refresh_from_db()
        self.assertFalse(self.device_a.is_active)
        self.assertIsNotNone(self.device_a.revoked_at)
        self.assertTrue(self.device_b.is_active)

    def test_policy_rejects_disallowed_provider(self):
        policy = AuthenticationPolicy.for_organization(self.organization)
        policy.allowed_providers = ["fido2"]
        policy.save(update_fields=["allowed_providers"])
        self.assertFalse(policy.allows_provider("windows_hello"))
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_models -v 2`

Expected: FAIL because the app data model does not exist.

- [ ] **Step 3: Implement state models and checked migrations**

Create UUID-keyed credentials and challenges. Credential fields are `user`, `device`, provider, unique binary `credential_id`, binary `credential_public_key`, `sign_count`, `credential_device_type`, `credential_backed_up`, metadata, activity/revocation fields, and timestamps. Challenge fields are exact user/device/provider/purpose, SHA-256 `challenge_hash`, timestamps, and metadata. Add `DeviceRequestNonce(device, nonce_hash, expires_at)` with a unique `(device, nonce_hash)` constraint, a one-policy-per-organization constraint, and nullable audit references with named event/reason choices. Add only nullable `Device.revoked_at`; preserve existing `is_active` behavior.

Policy defaults are `["windows_hello", "fido2", "passkey"]` and `user_verification`. `revoke_device()` sets inactive/revoked and records `DEVICE_REVOKED`; `credential.revoke()` records `CREDENTIAL_REVOKED`.

- [ ] **Step 4: Verify migrations and tests**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py makemigrations --check && PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py migrate && PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_models -v 2`

Expected: PASS.

### Task 3: Verify signed device requests and reject request-nonce replay

**Files:**

- Create: `apps/authentication/services/device_requests.py`
- Create: `apps/authentication/tests/test_device_requests.py`

**Interfaces:**

- Produces `canonical_request_payload(method, path, body, timestamp, nonce, device_id)` and `authenticate_signed_device_request(request) -> Device`.
- Raises `DeviceRequestAuthenticationError(code, status)` for Tasks 6-7.

- [ ] **Step 1: Write failing proof and replay tests**

```python
class SignedRequestTests(TestCase):
    def test_valid_rsa_pss_signature_authenticates_active_device(self):
        request = signed_request(self.device, b"{}")
        self.assertEqual(authenticate_signed_device_request(request).pk, self.device.pk)

    def test_reused_nonce_is_rejected_with_fresh_timestamp(self):
        authenticate_signed_device_request(signed_request(self.device, b"{}", nonce=NONCE))
        with self.assertRaisesRegex(DeviceRequestAuthenticationError, "REUSED_REQUEST_NONCE"):
            authenticate_signed_device_request(signed_request(self.device, b"{}", nonce=NONCE))

    def test_bad_signature_stale_timestamp_disabled_device_and_certificate_mismatch_fail(self):
        for request, code in invalid_envelopes(self.device):
            with self.subTest(code=code), self.assertRaisesRegex(DeviceRequestAuthenticationError, code):
                authenticate_signed_device_request(request)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_device_requests -v 2`

Expected: FAIL because signed-request authentication is absent.

- [ ] **Step 3: Implement canonical bytes, key proof, and atomic nonce creation**

```python
def canonical_request_payload(method, path, body, timestamp, nonce, device_id):
    return (
        "BIOGUARD-AGENT-REQUEST-V1\\n"
        f"{method.upper()}\\n{path}\\n{hashlib.sha256(body).hexdigest()}\\n"
        f"{timestamp}\\n{nonce}\\n{device_id}\\n"
    ).encode("utf-8")
```

Require the five documented headers. Decode a minimum-16-byte base64url nonce; lock the exact `pc_id + cert` device; reject stale timestamp, inactive/revoked device/org, invalid association, missing PEM SubjectPublicKeyInfo, and unsupported key types. Verify RSA PSS SHA-256, ECDSA SHA-256, or Ed25519 by the actual public-key type. In `transaction.atomic()`, save the nonce hash and convert unique-constraint `IntegrityError` into `REUSED_REQUEST_NONCE` from a nested savepoint.

- [ ] **Step 4: Add concurrency coverage and run it**

```python
def test_simultaneous_identical_envelopes_accept_exactly_one(self):
    results = run_in_parallel(2, lambda: authenticate_signed_device_request(self.request))
    self.assertEqual(results.count("accepted"), 1)
    self.assertEqual(results.count("REUSED_REQUEST_NONCE"), 1)
```

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_device_requests -v 2`

Expected: PASS. The unique database constraint is the portable race-safety proof; only run threaded timing assertions where the backend permits it.

### Task 4: Create secure WebAuthn challenges and genuine option generation

**Files:**

- Create: `apps/authentication/services/challenges.py`
- Create: `apps/authentication/services/webauthn.py`
- Create: `apps/authentication/tests/test_challenges.py`
- Create: `apps/authentication/tests/test_webauthn_options.py`

**Interfaces:**

- Produces `create_challenge()`, `load_locked_challenge()`, `recover_client_challenge()`, `registration_options()`, and `authentication_options()`.

- [ ] **Step 1: Write failing challenge/options tests**

```python
class ChallengeTests(TestCase):
    def test_uses_32_secure_bytes_and_retains_only_hash(self):
        record, challenge = create_challenge(self.user, self.device, "webauthn_authentication", "windows_hello")
        self.assertEqual(len(challenge), 32)
        self.assertEqual(record.challenge_hash, hashlib.sha256(challenge).hexdigest())
        self.assertFalse(hasattr(record, "challenge"))

    def test_expired_consumed_wrong_purpose_and_wrong_device_are_rejected(self):
        for code, kwargs in invalid_challenge_cases(self.challenge):
            with self.subTest(code=code), self.assertRaisesRegex(ChallengeValidationError, code):
                load_locked_challenge(**kwargs)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_challenges apps.authentication.tests.test_webauthn_options -v 2`

Expected: FAIL because challenge/options services are absent.

- [ ] **Step 3: Implement challenge state and library options**

`create_challenge()` calls `secrets.token_bytes(32)`, stores only its hash, and expires it in five minutes. `load_locked_challenge()` uses `select_for_update()` and validates exact user/device/provider/purpose/expiry/consumption state. `recover_client_challenge()` only decodes `clientDataJSON` to recover the challenge, uses `hmac.compare_digest` on its hash, then lets the library verify the same expected challenge cryptographically. Generate `generate_registration_options` and `generate_authentication_options` using explicit RP settings, policy-required user verification, and only active current-device credentials.

- [ ] **Step 4: Run tests**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_challenges apps.authentication.tests.test_webauthn_options -v 2`

Expected: PASS.

### Task 5: Complete genuine WebAuthn registration

**Files:**

- Modify: `apps/authentication/services/webauthn.py`
- Create: `apps/authentication/tests/test_registration.py`

**Interfaces:**

- Produces `complete_registration(device, user, provider, challenge_id, response) -> AuthenticationCredential`.

- [ ] **Step 1: Write failing genuine-registration tests**

```python
def test_verified_registration_persists_only_library_verified_material(self):
    credential = complete_registration(
        self.device, self.user, "windows_hello", self.challenge.challenge_id, VALID_REGISTRATION_RESPONSE
    )
    self.assertEqual(credential.device, self.device)
    self.assertTrue(credential.is_active)
    self.assertGreater(len(credential.credential_public_key), 0)

def test_wrong_rp_wrong_origin_invalid_response_and_replay_are_rejected(self):
    for response, code in invalid_registration_cases(self.challenge):
        with self.subTest(code=code), self.assertRaisesRegex(RegistrationError, code):
            complete_registration(self.device, self.user, "windows_hello", self.challenge.challenge_id, response)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_registration -v 2`

Expected: FAIL because completion does not exist.

- [ ] **Step 3: Implement verification and locked consumption**

In one transaction lock the registration-purpose record; recover/hash-match the expected challenge; enforce active user/device and policy; invoke `parse_registration_credential_json` and `verify_registration_response` with explicit RP ID/origin and required user verification. Store only verification result credential ID/public key/counter/device type/backup flag. Set `consumed_at` only after verification and audit `CREDENTIAL_REGISTERED`. Map malformed/invalid library exceptions to stable `INVALID_ASSERTION` without their raw text.

- [ ] **Step 4: Add duplicate-completion test and verify**

```python
def test_two_completion_attempts_create_one_credential(self):
    results = run_in_parallel(2, self.complete_same_valid_registration)
    self.assertEqual(AuthenticationCredential.objects.count(), 1)
    self.assertEqual(results.count("success"), 1)
    self.assertEqual(results.count("REPLAYED_CHALLENGE"), 1)
```

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_registration -v 2`

Expected: PASS.

### Task 6: Complete genuine assertions and expose the four new API routes

**Files:**

- Create: `apps/authentication/views.py`
- Modify: `apps/authentication/urls.py`
- Modify: `apps/authentication/services/webauthn.py`
- Create: `apps/authentication/tests/test_assertions.py`
- Create: `apps/authentication/tests/test_api.py`

**Interfaces:**

- Produces `POST /api/agent/auth/challenge/`, `/credentials/register/options/`, `/credentials/register/complete/`, and `/assertion/verify/`.

- [ ] **Step 1: Write failing assertion/API tests**

```python
def test_valid_assertion_consumes_once_updates_counter_and_audits(self):
    result = complete_authentication(self.device, self.user, self.credential, self.challenge.challenge_id, VALID_ASSERTION)
    self.challenge.refresh_from_db()
    self.credential.refresh_from_db()
    self.assertTrue(result.user_verified)
    self.assertIsNotNone(self.challenge.consumed_at)
    self.assertEqual(self.credential.sign_count, 5)

def test_new_api_requires_device_proof_before_user_resolution(self):
    response = self.client.post("/api/agent/auth/challenge/", data={"user_id": self.user.id})
    self.assertEqual(response.status_code, 401)
    self.assertEqual(response.json()["code"], "INVALID_DEVICE_SIGNATURE")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_assertions apps.authentication.tests.test_api -v 2`

Expected: FAIL because the APIs/completion function are absent.

- [ ] **Step 3: Implement locked assertion verification and views**

Lock challenge/credential/device together, validate provider/ownership/status/policy, recover/hash-match authentication-purpose challenge, then call `parse_authentication_credential_json` and `verify_authentication_response` with stored public key/counter plus explicit RP settings. On success update counter exactly from the library result (zero is not independently a compromise), last-used, consumed timestamp, and `AUTH_SUCCESS`. On failure leave challenge unconsumed and write `AUTH_FAILED`/normalized reason. Views safely parse JSON, authenticate signed device before user lookup, scope the user to device organization, and return only stable code/detail fields.

- [ ] **Step 4: Verify new and legacy API compatibility**

```python
def test_health_and_legacy_device_status_contract_is_unchanged(self):
    self.assertEqual(self.client.get("/api/health/").json(), {"ok": True})
    response = self.client.get("/api/agent/device/status/", {"pc_id": "unknown"})
    self.assertEqual(response.status_code, 404)
    self.assertEqual(response.json()["status"], "blocked_device")
```

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_assertions apps.authentication.tests.test_api apps.agent -v 2`

Expected: PASS.

### Task 7: Issue fail-closed signed offline policies and publish the Agent contract

**Files:**

- Create: `apps/authentication/services/offline_policy.py`
- Modify: `apps/authentication/views.py`
- Modify: `apps/authentication/urls.py`
- Create: `apps/authentication/tests/test_offline_policy.py`
- Create: `docs/agent-auth-contract.md`

**Interfaces:**

- Produces `POST /api/agent/auth/offline-policy/` and a contract that specifies trusted key provisioning and rotation.

- [ ] **Step 1: Write failing offline policy tests**

```python
@override_settings(OFFLINE_POLICY_SIGNING_PRIVATE_KEY_PEM=None)
def test_missing_key_returns_503_without_policy(self):
    response = self.signed_post("/api/agent/auth/offline-policy/", {"user_id": self.user.id})
    self.assertEqual(response.status_code, 503)
    self.assertEqual(response.json()["code"], "OFFLINE_POLICY_SIGNING_UNAVAILABLE")
    self.assertNotIn("policy", response.json())

def test_configured_ed25519_key_signs_versioned_policy(self):
    payload = issue_offline_policy(self.device, self.user)
    verify_with_provisioned_public_key(payload["signing_input"], payload["signature"])
    self.assertEqual(payload["algorithm"], "Ed25519")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_offline_policy -v 2`

Expected: FAIL because the offline signer is absent.

- [ ] **Step 3: Implement the dedicated-key Ed25519 signer**

Load only an Ed25519 PEM from `OFFLINE_POLICY_SIGNING_PRIVATE_KEY_PEM` and configured `OFFLINE_POLICY_SIGNING_KEY_ID`. Fail with `503 OFFLINE_POLICY_SIGNING_UNAVAILABLE` for absent/bad/wrong-type key. Sign the specified versioned JSON policy in documented canonical UTF-8 form using `cryptography`. Return payload, detached base64url signature, `algorithm: "Ed25519"`, and key ID. Do not return a public key, use a device/Fernet key, or emit an unsigned policy.

- [ ] **Step 4: Document precise Agent contract and verify**

Write method/path/header/request/response/error schema for every new endpoint. Include Windows Win32 WebAuthn base64url-JSON translation, canonical request bytes, supported PEM algorithms, nonce and challenge separation, RP configuration, assertion/registration requirements, and offline trust-anchor distribution/key rotation. State legacy flow classifications and non-goals.

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication.tests.test_offline_policy apps.authentication.tests.test_api -v 2`

Expected: PASS.

### Task 8: Run end-to-end verification

**Files:**

- Modify only a file introduced by Tasks 1-7 if a check exposes an actual defect.

**Interfaces:**

- Consumes all preceding work and proves migration/test/compatibility integrity.

- [ ] **Step 1: Check model/migration integrity**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py makemigrations --check && PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py migrate --plan && PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py check`

Expected: no model drift and no system check errors.

- [ ] **Step 2: Run new security tests**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test apps.authentication -v 2`

Expected: PASS, covering valid and invalid ceremonies, RP/origin, counters, device nonce replay, challenge replay, state/policy, audit, and offline signing.

- [ ] **Step 3: Run repository suite and inspect compatibility diff**

Run: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python manage.py test -v 2 && git diff --check && git diff -- project/urls.py apps/agent apps/biometrik apps/org`

Expected: PASS. The only existing routing change is a root include for the new app; legacy handlers remain untouched.
