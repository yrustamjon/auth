"""Explicit VM-only administration. No side effects at import time."""
import argparse
from pathlib import Path
import sys

SERVICE_NAME = 'BioGuardAuthority'
CLIENT_PIPE_ACCESS = 0x00100003  # SYNCHRONIZE | FILE_READ_DATA | FILE_WRITE_DATA


def service_sddl(service_sid):
    return f'D:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GA;;;{service_sid})(A;;0x4;;;IU)'


def pipe_sddl(service_sid, user_sid):
    # Generic write includes CREATE_PIPE_INSTANCE; clients must never get it.
    return f'D:P(A;;GA;;;SY)(A;;GA;;;{service_sid})(A;;0x{CLIENT_PIPE_ACCESS:x};;;{user_sid})'


def validate_install_tree(executable, program_files):
    """Only the dedicated Program Files directory; refuse all reparse points."""
    executable = Path(executable)
    expected = Path(program_files) / SERVICE_NAME
    if executable.name != 'BioGuardService.exe' or executable.parent.resolve() != expected.resolve():
        raise ValueError('Install the standalone build in Program Files/BioGuardAuthority')
    root = executable.parent
    paths = [root, *root.rglob('*')]
    for item in [*root.parents, *paths]:
        if item.lstat().st_file_attributes & 0x400:
            raise ValueError('Reparse points are not allowed in the installation tree')
    if not executable.is_file():
        raise ValueError('Service executable is missing')
    return paths


def _descriptor(sddl):
    import win32security
    return win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(sddl, 1)


def _service_sid():
    import win32security
    sid, _, _ = win32security.LookupAccountName(None, 'NT SERVICE\\' + SERVICE_NAME)
    return win32security.ConvertSidToStringSid(sid)


def _protect_files(paths, service_sid):
    import win32security
    descriptor = _descriptor(f'D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FRFX;;;{service_sid})')
    owner = win32security.ConvertStringSidToSid('S-1-5-32-544')
    for path in paths:
        win32security.SetNamedSecurityInfo(
            str(path), win32security.SE_FILE_OBJECT,
            win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION |
            win32security.OWNER_SECURITY_INFORMATION,
            owner, None, descriptor.GetSecurityDescriptorDacl(), None)


def _configure_service():
    import win32service
    import win32security
    manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
    try:
        handle = win32service.OpenService(manager, SERVICE_NAME, win32service.SERVICE_ALL_ACCESS)
        try:
            win32service.ChangeServiceConfig2(handle, win32service.SERVICE_CONFIG_SERVICE_SID_INFO,
                                             win32service.SERVICE_SID_TYPE_UNRESTRICTED)
            win32service.ChangeServiceConfig2(handle, win32service.SERVICE_CONFIG_FAILURE_ACTIONS,
                {'ResetPeriod': 86400, 'RebootMsg': None, 'Command': None,
                 'Actions': [(win32service.SC_ACTION_RESTART, 5000),
                             (win32service.SC_ACTION_RESTART, 30000),
                             (win32service.SC_ACTION_NONE, 0)]})
            win32service.ChangeServiceConfig2(handle, win32service.SERVICE_CONFIG_FAILURE_ACTIONS_FLAG, True)
            win32service.SetServiceObjectSecurity(handle, win32security.DACL_SECURITY_INFORMATION,
                                                  _descriptor(service_sddl(_service_sid())))
            # Only enable boot startup after recovery and access controls succeed.
            win32service.ChangeServiceConfig(handle, win32service.SERVICE_NO_CHANGE,
                win32service.SERVICE_AUTO_START, win32service.SERVICE_NO_CHANGE,
                None, None, 0, None, None, None, None)
        finally:
            win32service.CloseServiceHandle(handle)
    finally:
        win32service.CloseServiceHandle(manager)


def service_cli(service_class, argv=None):
    parser = argparse.ArgumentParser(description='BioGuard service VM administration')
    parser.add_argument('command', choices=('install', 'start', 'stop', 'remove', 'status'))
    parser.add_argument('--vm-test', action='store_true')
    args = parser.parse_args(argv)
    import win32serviceutil
    if args.command == 'status':
        print(win32serviceutil.QueryServiceStatus(SERVICE_NAME))
        return 0
    if not args.vm_test:
        parser.error('Mutating commands require --vm-test in a disposable Windows VM')
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        parser.error('Run the VM administration command elevated')
    if args.command == 'install':
        if not getattr(sys, 'frozen', False):
            parser.error('Install only the standalone frozen build')
        # Obtain the actual Windows known-folder path, not a caller-controlled env var.
        import win32com.shell.shell as shell
        import win32com.shell.shellcon as shellcon
        program_files = shell.SHGetFolderPath(0, shellcon.CSIDL_PROGRAM_FILES, None, 0)
        paths = validate_install_tree(sys.executable, program_files)
        import win32service
        win32serviceutil.InstallService(
            'platform_adapters.windows.service_host.BioGuardService', SERVICE_NAME,
            service_class._svc_display_name_, userName='NT AUTHORITY\\LocalService',
            exeName=sys.executable, description=service_class._svc_description_,
            startType=win32service.SERVICE_DEMAND_START)
        try:
            sid = _service_sid()
            _protect_files(paths, sid)
            _configure_service()
        except Exception:
            # Security/configuration failure rolls back the never-started installation.
            win32serviceutil.RemoveService(SERVICE_NAME)
            raise
    elif args.command == 'start':
        win32serviceutil.StartService(SERVICE_NAME)
    elif args.command == 'stop':
        win32serviceutil.StopService(SERVICE_NAME)
    else:
        win32serviceutil.RemoveService(SERVICE_NAME)
    return 0
