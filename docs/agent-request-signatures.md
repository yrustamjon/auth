# BioGuard request authentication v1

This is a coordinated breaking change: deploy backend and agent together, then
re-enroll older agents with a new organization token. No unsigned compatibility
switch exists. Previous open sessions without device binding must be restarted.
Browser-approved activation requires an unused, unexpired organization token,
registered device in that organization, RSA >=2048 public key and key possession.
Revoked devices/inactive organizations cannot enroll. Already enrolled devices
cannot silently rotate their key with another token. Server persistence and token
claim are transactional. Client verifies DPAPI availability before consuming a
server token; network loss or disk failure after the server commits still needs
administrator recovery/new enrollment token, not an unsigned fallback.

The agent signs RSA-PSS/SHA256 with MGF1-SHA256 and a 32-byte salt. Headers:
X-BioGuard-Version=1, X-PC-ID, X-Cert-ID, X-Timestamp (UTC Unix seconds), X-Nonce
(lowercase random hex, 32–128 characters), X-Signature (standard base64).
Signature bytes cover these UTF-8 fields joined by LF, without trailing LF:

```
BIOGUARD/1
UPPERCASE_METHOD
CANONICAL_PATH_QUERY
LOWERCASE_HEX_SHA256_OF_EXACT_BODY_BYTES
PC_ID
CERT_ID
TIMESTAMP
NONCE
```

Path percent escapes are decoded strictly and re-encoded with safe `/~-._`;
query is parsed preserving duplicates, order and blank values, then urlencode'd.
The query order is not sorted because Django uses the last duplicate value.
The body is never reserialized for verification. Reject newlines in fields.
Agent and backend copies of signatures.py must remain wire-identical. A proxy
must not rewrite signed method, target, query or body. TLS verification stays on.

Timestamps accept at most 300 seconds old or 30 seconds future. Nonces are
claimed in the database with a unique (certificate_id,nonce) constraint; validity
expires at timestamp+301 seconds. Duplicate claims return 409. SQLite writer
contention fails closed; production multiworker use should use PostgreSQL.
Expired records are cleaned on claims; also schedule
`python manage.py cleanup_request_nonces` at least every five minutes.

Desktop route inventory: every /api/agent/ route (including check-pc,
validate-code, device status, session/start, face/fingerprint status) and
/api/face/agent/check/ requires signed enrolled credentials. Unsupported future
routes do not create unsigned exceptions. /api/agent/activate/ is only bootstrap:
use the same envelope with X-Cert-ID=bootstrap and the supplied public key. The
one-use organization token provides bootstrap authorization, not the certificate.
/api/health/ is a public health check and provides no authority.

Sessions bind to a device FK; signed identity must match payload/query device,
active organization/user and the session's device/user. Certificate lookup binds
the stored public key and PC ID; revoked/inactive/un-enrolled devices fail closed.
Phone pages and face submission use a session capability and must actually match
registered face data; this does not establish liveness or suitability for native
Windows enforcement. Phone fingerprint rawId comparison was an authorization bypass. It is replaced
with WebAuthn registration/assertion verification (webauthn 2.7.1): server-issued
challenges, exact PUBLIC_SITE_URL origin/RP-ID, user presence and verification,
stored credential public keys/counters and atomic ceremony consumption. Legacy
credentials without verified public keys/RP binding must be re-registered.
PUBLIC_SITE_URL must be an HTTPS origin or loopback HTTP origin. Registration
start requires an authenticated administrator assigned to the user's organization;
its short-lived random session capability authorizes the phone ceremony.
WebAuthn UV can use device PIN or other authenticator verification; it does not
prove that a physical fingerprint was used. No native Windows login enforcement
or tested face liveness is implied. Production multiworker database behavior,
phone/browser/hardware and Windows acceptance still need target-system evidence.
