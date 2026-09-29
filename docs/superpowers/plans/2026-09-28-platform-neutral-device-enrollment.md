# Platform-Neutral Device Enrollment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Django device and QR enrollment implementation match the approved platform-neutral device architecture while preserving legacy API compatibility.

**Architecture:** Keep one `common.Device` table for all platforms and expose canonical `device_id`/`public_key` domain names over the existing `pc_id`/`device_public_key` storage contracts. Rename the browser session model to canonical `DeviceEnrollmentSession`, retain operational fields required by the QR flow, and keep pending/resolution state in that session. Approval creates an inactive `browser_approved` device; credential enrollment and activation remain out of scope.

**Tech Stack:** Django, Django REST Framework, SQLite test database, Django templates, vanilla JavaScript.

**Spec:** `docs/superpowers/specs/2026-09-28-platform-neutral-device-enrollment-design.md`

## Global Constraints

- Use one shared `Device` model; do not create Windows, macOS, or Linux device tables.
- Session statuses are exactly `pending`, `approved`, `rejected`, `expired`, and `cancelled`.
- Browser approval persists `browser_approved` and `is_active=False`.
- QR bearer secrets remain hashed at rest.
- Existing legacy device and agent endpoints continue working through compatibility aliases.
- `DeviceCredential`, attestation verification, and final activation are not implemented in this phase.

## Review Focus

- Legacy callers using `pc_id`, `license`, and `device_public_key` still receive the same behavior; pin this in device API regression tests.
- A browser-approved device cannot be activated or edited through legacy paths; pin this in device and activation tests.
- A repeated or expired session mutation returns the correct conflict/expiry response; pin this in session lifecycle tests.
- Location submitted during approval is stored on the resulting device; pin this in approval tests.
- Platform-specific identifiers reject unknown keys and mismatched primary IDs; pin this in validation tests.

### Task 1: Canonical Device domain fields

**Files:**
- Modify: `apps/common/models.py`
- Create: `apps/common/migrations/0013_platform_neutral_device_contract.py`
- Test: `apps/device/tests.py`

**Interfaces:**
- Preserve database storage and legacy properties for `pc_id`, `license`, and `device_public_key`.
- Add canonical writable `device_id` and `public_key` accessors used by new code.
- Keep `platform`, `identifiers`, `attestation_status`, and enrollment lifecycle choices.

- [ ] **Step 1: Write failing model tests** for canonical field access, platform-specific identifier persistence, and `browser_approved` default inactive behavior.
- [ ] **Step 2: Run `PYTHONDONTWRITEBYTECODE=1 /Users/macbook/Desktop/auth/venv/bin/python manage.py test apps.device.tests.DevicePlatformApiTests -v 2` and confirm the new assertions fail for the missing canonical contract.
- [ ] **Step 3: Implement the smallest model/migration change**, keeping legacy database columns and adding only required canonical fields or properties.
- [ ] **Step 4: Run the focused tests and `manage.py makemigrations --check` until both pass.**
- [ ] **Step 5: Run `git diff --check` and record the task as complete.**

### Task 2: Canonical DeviceEnrollmentSession model

**Files:**
- Modify: `apps/device/models.py`
- Create: `apps/device/migrations/0003_device_enrollment_session_contract.py`
- Test: `apps/device/tests.py`

**Interfaces:**
- `DeviceEnrollmentSession` becomes the canonical Django model import.
- Existing `BrowserEnrollmentSession` imports remain a compatibility alias.
- Canonical properties expose `session_id`, `browser_session_hash`, `platform_claimed`, and `device_metadata`.

- [ ] **Step 1: Write failing tests** importing `DeviceEnrollmentSession`, checking the five exact statuses, canonical properties, hashed display code, and timestamp fields.
- [ ] **Step 2: Run the focused session tests and verify the failure is caused by the non-canonical model contract.**
- [ ] **Step 3: Rename the model through a Django state/database migration or a stable proxy-compatible implementation without dropping existing data.**
- [ ] **Step 4: Update imports and run all browser enrollment tests.**
- [ ] **Step 5: Run `manage.py makemigrations --check` and `git diff --check`.**

### Task 3: Enrollment state transitions and approval persistence

**Files:**
- Modify: `apps/device/browser_enrollment.py`
- Modify: `apps/device/browser_views.py`
- Modify: `apps/device/urls.py`
- Test: `apps/device/tests.py`

**Interfaces:**
- Session creation remains `POST /api/devices/browser-enrollment/session/`.
- Target page remains `/device/scan`.
- Admin approval entry remains `/device-enroll/<token>` and scanner remains `/devices/add/qr`.
- `resolve(..., action=...)` remains the single transition function.

- [ ] **Step 1: Write failing tests** for supplied location persistence, duplicate approval rejection, replay rejection, expiry, and resulting `browser_approved`/inactive device state.
- [ ] **Step 2: Run those tests and confirm the location and canonical contract failures.**
- [ ] **Step 3: Update session payload and identity/approval handling** so location is explicitly supplied and copied to `Device.location`; use canonical session imports while retaining aliases.
- [ ] **Step 4: Run the full `apps.device` test module and fix only regressions caused by the contract update.**
- [ ] **Step 5: Run `git diff --check`.**

### Task 4: Admin templates and platform-specific forms

**Files:**
- Modify: `templates/devices.html`
- Modify: `templates/device_scan.html`
- Modify: `templates/device_enroll_approval.html`
- Modify: `templates/device_qr_scanner.html`
- Modify: `static/js/devices.js`
- Test: `apps/device/tests.py`

**Interfaces:**
- Manual add form displays Windows `MachineGUID`/Product ID, macOS `Platform UUID`/Serial, and Linux `Machine ID`/Product UUID.
- QR buttons use the existing route names and session API.

- [ ] **Step 1: Add failing template contract assertions** for the three platform field sets and all requested URLs.
- [ ] **Step 2: Run the UI contract tests and verify missing labels/fields fail.**
- [ ] **Step 3: Update template and JavaScript field mapping** to send canonical `device_id`, `identifiers`, and `location`, while accepting legacy response keys.
- [ ] **Step 4: Run UI contract tests and browser enrollment tests.**
- [ ] **Step 5: Run `git diff --check`.**

### Task 5: Full verification and documentation

**Files:**
- Modify: `docs/browser-device-registration.md`
- Test: `apps/device/tests.py`, project test suite

- [ ] **Step 1: Add any remaining regression tests** identified by the Review Focus list.
- [ ] **Step 2: Run `PYTHONDONTWRITEBYTECODE=1 /Users/macbook/Desktop/auth/venv/bin/python manage.py makemigrations --check`.**
- [ ] **Step 3: Run `PYTHONDONTWRITEBYTECODE=1 /Users/macbook/Desktop/auth/venv/bin/python manage.py test -v 2`.**
- [ ] **Step 4: Update the registration documentation with canonical names, lifecycle, and the explicit out-of-scope `DeviceCredential` phase.**
- [ ] **Step 5: Run `git diff --check` and report any pre-existing unrelated failures separately.**

