# SDD ledger — plan: docs/superpowers/plans/2026-10-10-frontend-modernization.md
User approved spec, plan and native execution.
Baseline: Vite build passes. Existing venv points to inaccessible WindowsApps Python; use installed PostgreSQL Python.
Ruling: Work in requested checkout — sandbox excludes .git writes; preserve unrelated changes and avoid commits until reviewable.
Pre-flight: AppShell shared by login/CRUD; preserve toast contexts. Collection adapters shared by dashboards/CRUD. QR continuation uses validated local redirects. Phone links use frontend public origin.
Tasks 1–6 completed: shared responsive shell, session/auth contracts, CRUD/dashboard modernization, biometrics/phone flow, public QR enrollment/approval, tests and setup docs.

Latest clarification implemented: public `/`, `/product`, `/downloads`, `/guide`, anonymous `/device/scan`; login is a modal on `/?login=admin` or `/?login=superadmin`. Legacy login links preserve continuation. Downloads use actual per-session helper bundles; full Agent installer files are not supplied.

Verification: lint/build pass; 11 Node tests and 15 Playwright tests pass. Django existing/new tests: 71 pass. Desktop/mobile screenshots inspected. Browser APIs mocked, backend integration uses test DB.

Final independent review: four Important findings fixed with regressions (DRF 403 expired session, admin API error falsely empty, duplicate organization toggle, unsupported create status). Mobile keyboard navigation fixed. Login API 403 excluded from session redirects.

Deferred Minor: approval polling stops on transient API error; refresh resumes. Physical camera/WebAuthn/native helper and deployed HTTPS/proxy are environment verification limits. Existing backend warnings/dependency advisories left outside scope. Unsupported USB/external biometric insertion UI removed rather than simulated.

Original venv Python target is stale; tools/run_django.py supports installed pgAdmin Python with local dependencies. README documents public origin, helper binaries and production proxy setup. Unrelated user changes preserved; no commits made.

