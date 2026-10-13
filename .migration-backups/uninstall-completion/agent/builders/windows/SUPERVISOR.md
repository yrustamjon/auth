# Standard Windows process supervision

The normal installer includes `BioGuardSupervisor.exe`, `BioGuardWatchdog.exe`, and the existing GUI agent. The SCM service runs as LocalSystem solely to start the fixed watchdog executable in the installed desktop user's active Windows session. The watchdog and GUI run using that user's token and credentials. No arbitrary commands or remote shells are accepted.

The service verifies the machine installation path and target user SID, refuses reparse points, and monitors the exact watchdog executable in that user's session. SCM recovery restarts the service on failures. Administrators retain standard stop/remove rights; this is not PPL/ELAM and does not resist a fully privileged attacker.

The watchdog attaches to an existing GUI agent or launches the installed GUI. Unexpected termination triggers an observed-exit event and a restart attempt. Failed starts back off to a maximum five-minute interval. A signed server pause permission suppresses restarts during the interval; it does not force-close a running GUI. When the permission expires, an absent GUI can be started again. In an outage the watchdog retains its most recently obtained policy; a newly issued pause cannot be known until connectivity returns.

SIMULATE and EXIT remain enabled. EXIT writes a matching process journal entry; the watchdog respects it for the current watchdog session. Starting the GUI manually resumes observation. Restarting the watchdog or logging in again also resumes ordinary startup.

Before replacing an existing installation, Setup stops the service. Only after activation verification, file copying, and preparation of the recovery helper does it install/start supervision. Authorized uninstall confirms the server operation, removes the SCM service, then closes the installed GUI and deletes files. The retained native helper can remove the service even if the service executable is damaged.

## Owner emergency recovery

Run `recover-supervisor.cmd` in the install folder as administrator. It removes supervision and stops only the installed GUI; it retains identity credentials and does not delete files. The native GUI stop first requests normal window closure, allowing desktop cleanup, and waits. If forced termination is needed it waits for the exact process and restores the taskbar.

If the application files themselves cannot execute, use Windows Services (`services.msc`) to stop/disable **ADAuth Agent Supervisor** (`BioGuardSupervisor`) as administrator, then repair/reinstall the application. No Windows services other than this named application service are changed. Authorized reinstall can restore the service. Do not claim hardware-level, administrator-proof, or native Windows login enforcement.

Deployment verification still requires a disposable Windows VM: install, end GUI process, end watchdog, logoff/logon, grant/expire a pause, use EXIT, upgrade, emergency stop, interrupted uninstall, and reinstall. Unit/API tests and successful compilation do not substitute for these native installation tests.
