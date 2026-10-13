# Approved registration flow

User approved separate personal workspaces while retaining mandatory organization relations, then required PC identity during personal signup and review for company signup. Existing company PC QR enrollment remains subject to that company's administrator approval.

Implementation: add organization kind and review metadata (existing organizations default company/approved); atomic public registration; personal signup consumes only this browser's unexpired completed native-helper scan, creates owner/role/user/device without company review; company signup creates an inactive pending organization and isolated owner, with authenticated status page. System administrators explicitly approve/reject via review queue. Pending organizations cannot use management APIs; global APIs require system administrator; tenant record mutations stay scoped. Signup uses CSRF and Django password validators.

Frontend: root registration modal with personal/company choice, personal PC helper step before account submission, company pending status, system review queue. Preserve public site, anonymous QR creation, existing agent enrollment and hardware protocols.

Verification: registration ownership/CSRF/rollback/duplicate/isolation/pending-login/decision tests; UI flow tests; full relevant Django suites, lint/build/Node/Playwright. Apply additive migration locally after checks; no git commits or unrelated user-change edits.

Completed: additive migration applied after consistent SQLite backup in ignored frontend/artifacts. Existing companies remain company/approved. 79 Django tests pass, plus 2 download catalog tests; lint/build pass, 11 Node tests and 19 browser tests pass. Independent reviews found no Critical/Important issues. Minor personal helper copy, tab state persistence, and inactive-status polling were corrected.

Latest user correction: product download must be the real Agent from sibling ../agent/releases. Added public catalog/installer streaming endpoints using VERSION + manifest and actual package presence/size, filename/platform allowlists and resolved path containment. Windows 1.0.3 installer 60,825,007 bytes selected; SHA-256 independently matches manifest. Linux/macOS 0.0.0 placeholders unavailable. Sibling repository is read-only; its AGENTS.md constraints and pre-release label retained. Future package publishing must verify manifest checksum. Helper remains only in registration/QR identity flow.
