# Platform-Neutral Device Enrollment Design

## Goal

Align the device registration backend and Django templates with one platform-neutral `Device` model and a separate browser QR enrollment session. Browser approval creates a disabled, `browser_approved` device; cryptographic agent enrollment and activation remain a later phase.

## Device model

`Device` is shared by Windows, macOS, and Linux. Platform-specific identity is represented by `platform` and the JSON `identifiers` field; no platform-specific device tables are introduced.

The canonical fields are:

- `organization`
- `platform`
- `device_id`
- `identifiers`
- `location`
- `public_key`
- `attestation_status`
- `enrollment_status`
- `is_active`
- `enrolled_at`
- `revoked_at`
- `created_at` and `updated_at`

The existing `pc_id`, `license`, and `device_public_key` contracts are retained as compatibility aliases during migration because legacy agent and admin endpoints still consume them. New browser enrollment code uses canonical names. A device remains uniquely identified within an organization by `device_id`.

Device enrollment lifecycle:

```text
browser_approved -> agent_enrolled -> active
```

Manual registration remains supported through the compatibility path. Browser approval always creates `browser_approved` with `is_active=False`, no public key, and no attestation proof.

## Browser enrollment session

`DeviceEnrollmentSession` is the canonical model name for a short-lived browser QR session. It stores only hashed bearer/session secrets and non-secret claimed device metadata.

Required fields:

- `session_id`
- `token_hash`
- `browser_session_hash`
- `platform_claimed`
- `device_metadata`
- `display_code_hash`
- `status`
- `expires_at`
- `claimed_at`
- `approved_by`
- timestamps

The implementation may retain operational fields needed by the flow, including scan token hash, organization, claimant, identity receipt, resolved time, and the resulting device relation. The public API and domain helpers expose the canonical names above.

Session statuses are exactly `pending`, `approved`, `rejected`, `expired`, and `cancelled`. A session can only be resolved once. Expiry is enforced during reads and mutations.

## Frontend flow

- Admin panel: Devices list, manual add, and QR add.
- Platform selection changes the manual form fields.
- Target computer opens `/device/scan`.
- Admin phone opens `/device-enroll/<token>`.
- Admin QR entry starts at `/devices/add/qr`.

The target helper submits the platform primary identifier and allowed metadata. The admin sees the claimed metadata and explicitly approves or rejects it. Location is supplied by the approval flow and is persisted on the resulting device; it is never treated as cryptographic identity.

## Security and compatibility constraints

- QR URLs, scan tokens, display codes, and browser session identifiers are not stored in plaintext when they are bearer secrets.
- Browser approval is an administrative claim only. It does not prove hardware identity.
- Existing legacy activation endpoints cannot activate a `browser_approved` device.
- Public-key proof-of-possession, `DeviceCredential`, attestation verification, and final activation are out of scope for this change and remain the next phase.

## Acceptance criteria

1. Canonical model fields and domain properties match this document.
2. Existing legacy device endpoints and tests continue to work through compatibility aliases.
3. QR approval persists the canonical device identity, location, and browser-approved lifecycle state.
4. Session state transitions and expiry reject replay and invalid transitions.
5. Django templates expose the three requested URLs and platform-specific fields.
