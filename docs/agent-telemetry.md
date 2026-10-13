# Agent process events and connection monitoring

The Windows agent journals process start, observed restart, graceful EXIT, and a previous process without a graceful-exit record. These events are statements from the signed agent, not proof that a particular person used Task Manager. Power loss and crashes can also leave an unfinished process record.

Events are stored in the installed user's `APPDATA/ADBioGuard/telemetry.sqlite3`. Requests to `POST /api/agent/telemetry/` use the existing device signature, timestamp and nonce verification. Only acknowledged event UUIDs are deleted from the local outbox. Offline reports are retried every 30 seconds. The server records receipt time separately from the agent's reported time and rejects client-supplied administrator/server event types.

`/agent-events` and `/personal/agent-events` show the latest 300 events in the current workspace. Warning events in the last 24 hours also appear in the administrator shell. Process IDs and Windows usernames are agent-reported context; they do not identify who terminated a process.

Devices are monitored after their first heartbeat. After 120 seconds without a heartbeat, the server records `connection_lost` once. Recovery records `connection_restored`. A recorded graceful exit has its own event and is not presented as an unexplained connection loss.

`POST /api/devices/<id>/pause-permission/` records the authorized administrator, reason and 0–240 minute interval. This grants permission and suppresses missing-connection alerts during that interval; it does not remotely close the desktop UI. Zero cancels the permission. The interval is checked against server time and expiration is recorded.

The event endpoint checks connection health while the panel is open. For monitoring without an open panel, run the configured Celery worker and Beat scheduler with the deployment's broker, or schedule `python manage.py check_agent_health` once per minute. This change does not provision a broker or install an OS scheduled task.

The Windows installer now includes the ordinary `BioGuardSupervisor` service and a per-user `BioGuardWatchdog.exe`. The service starts the watchdog under the enrolled user's active session; the watchdog observes the installed agent and restarts it after an unexpected exit, with retry backoff. Watchdog reports do not replace the agent's heartbeat. Logs describe observed process exits rather than attributing them to a person.

The signed `/api/agent/supervision/` policy suppresses restarts during an authorized pause or after device revocation/removal. Offline operation uses the last cached policy, so a newly granted server pause requires connectivity. Pre-release EXIT suppresses agent restarts for the current watchdog session. Authorized uninstall removes supervision before stopping the agent. Administrators retain normal Windows service controls and the installed `recover-supervisor.cmd` emergency helper. This does not implement PPL/ELAM or protection against a Windows administrator.

Install the rebuilt Windows package to enable supervision and telemetry; older installed EXEs remain unchanged. See the agent repository's `builders/windows/SUPERVISOR.md` for recovery steps and the required Windows VM installation, upgrade, pause, process termination and uninstall checks.
