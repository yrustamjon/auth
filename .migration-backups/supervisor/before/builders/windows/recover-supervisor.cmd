@echo off
rem Run as administrator. Stops supervision, without deleting credentials.
"%ProgramW6432%\AD BioGuard\BioGuardLifecycle.exe" --stop-supervisor
if errorlevel 1 exit /b 1
"%ProgramW6432%\AD BioGuard\BioGuardLifecycle.exe" --stop-agent --install-path "%ProgramW6432%\AD BioGuard"
exit /b %errorlevel%
