"""Local, first-instance pipe restricted to the verified native Setup process."""
import ctypes
import os
import re
import time
from pathlib import Path


def process_image_path(handle):
    from ctypes import wintypes
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    api.QueryFullProcessImageNameW.restype = wintypes.BOOL
    size = wintypes.DWORD(32768)
    buffer = ctypes.create_unicode_buffer(size.value)
    if not api.QueryFullProcessImageNameW(int(handle), 0, buffer, ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
    return buffer.value


def process_session(pid):
    from ctypes import wintypes
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    api.ProcessIdToSessionId.restype = wintypes.BOOL
    session = wintypes.DWORD()
    if not api.ProcessIdToSessionId(pid, ctypes.byref(session)):
        raise ctypes.WinError(ctypes.get_last_error())
    return session.value


def pipe_path(name):
    if not re.fullmatch(r'BioGuardLifecycle-[a-fA-F0-9-]{36}', name):
        raise ValueError('Invalid lifecycle pipe name')
    return '\\\\.\\pipe\\' + name


def serve(name, parent_pid, broker):
    import pywintypes
    import win32api
    import win32con
    import win32file
    import win32pipe
    import win32security
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetNamedPipeClientProcessId.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetNamedPipeClientProcessId.restype = wintypes.BOOL
    from .lifecycle import current_sid, is_elevated
    if is_elevated():
        raise OSError('Restart setup from the intended unelevated desktop')
    parent = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, parent_pid)
    sid = current_sid()
    descriptor = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(
        f'D:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GA;;;{sid})', win32security.SDDL_REVISION_1)
    attrs = pywintypes.SECURITY_ATTRIBUTES()
    attrs.SECURITY_DESCRIPTOR = descriptor
    pipe = win32pipe.CreateNamedPipe(pipe_path(name), win32pipe.PIPE_ACCESS_DUPLEX | 0x00080000,
        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_NOWAIT | 0x8,
        1, 65536, 65536, 0, attrs)
    client_connected = False
    try:
        while win32process_exit(parent) == 259:
            if not client_connected:
                try:
                    win32pipe.ConnectNamedPipe(pipe, None)
                    client_connected = True
                except pywintypes.error as error:
                    if error.winerror == 535:
                        client_connected = True
                    elif error.winerror not in (536, 232):
                        raise
                if client_connected:
                    actual = ctypes.c_ulong()
                    if not kernel.GetNamedPipeClientProcessId(int(pipe), ctypes.byref(actual)) or actual.value != parent_pid:
                        win32pipe.DisconnectNamedPipe(pipe)
                        client_connected = False
                        continue
            if client_connected:
                try:
                    _, raw = win32file.ReadFile(pipe, 65536)
                    if not raw:
                        time.sleep(.025)
                        continue
                    parts = raw.decode('utf-16-le').rstrip('\x00').split('\t', 1)
                    command, secret = parts[0], parts[1] if len(parts) > 1 else ''
                    if command == 'cancel':
                        break
                    result = broker.dispatch(command, secret)
                    fields = [str(result.get(key, '')).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                        for key in ('state', 'organization', 'device_uuid', 'target_sid', 'target_user', 'message')]
                    win32file.WriteFile(pipe, '\t'.join(fields).encode('utf-16-le'))
                except pywintypes.error as error:
                    if error.winerror in (109, 232, 233):
                        if error.winerror == 109:
                            win32pipe.DisconnectNamedPipe(pipe)
                            client_connected = False
                    else:
                        raise
            time.sleep(.025)
    finally:
        pipe.Close()
        parent.Close()
        broker.join()  # A bounded submitted activation may persist its result.


def win32process_exit(handle):
    import win32process
    return win32process.GetExitCodeProcess(handle)


def launch_for_installed_user(executable, arguments, target_sid, parent_pid, name):
    """Launch a limited helper using the exact installed user's live desktop token.

    No credential prompt/password storage; fails closed if that user is not logged
    into the same interactive session. Original-user Exec is unavailable in Inno
    Uninstall, so this adapter performs the explicit identity transfer.
    """
    import subprocess
    import win32api
    import win32con
    import win32process
    import win32security
    import win32profile
    import shutil
    from .lifecycle import is_elevated
    if not is_elevated() or not re.fullmatch(r'S-1-5-[0-9-]+', target_sid):
        raise OSError('Elevated native uninstaller and valid installed user required')
    pipe_path(name)
    folder = Path(os.environ['ProgramData']) / 'AD BioGuard' / 'lifecycle' / name
    folder.mkdir(parents=True, exist_ok=False)
    descriptor = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(
        f'D:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;FRFX;;;{target_sid})', win32security.SDDL_REVISION_1)
    win32security.SetFileSecurity(str(folder), win32security.DACL_SECURITY_INFORMATION, descriptor)
    destination = folder / 'BioGuardLifecycle.exe'
    shutil.copy2(executable, destination)
    win32security.SetFileSecurity(str(destination), win32security.DACL_SECURITY_INFORMATION, descriptor)
    parent_session = process_session(parent_pid)
    for pid in win32process.EnumProcesses():
        process = token = primary = None
        try:
            if process_session(pid) != parent_session:
                continue
            process = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            token = win32security.OpenProcessToken(process, win32con.TOKEN_QUERY | win32con.TOKEN_DUPLICATE)
            actual_sid = win32security.ConvertSidToStringSid(win32security.GetTokenInformation(token, win32security.TokenUser)[0])
            if actual_sid != target_sid or win32security.GetTokenInformation(token, win32security.TokenElevation):
                continue
            primary = win32security.DuplicateTokenEx(token, win32security.SecurityImpersonation,
                win32con.TOKEN_ALL_ACCESS, win32security.TokenPrimary)
            environment = win32profile.CreateEnvironmentBlock(primary, False)
            return _create_with_token(primary, destination, subprocess.list2cmdline([str(destination), *arguments]), environment)
        except (OSError, win32api.error):
            continue
        finally:
            for handle in (primary, token, process):
                if handle:
                    handle.Close()
    raise OSError('Log in as the installed desktop user before removing the agent')


def _create_with_token(token, executable, command_line, environment):
    from ctypes import wintypes
    class Startup(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('reserved', wintypes.LPWSTR), ('desktop', wintypes.LPWSTR),
            ('title', wintypes.LPWSTR), ('x', wintypes.DWORD), ('y', wintypes.DWORD), ('cx', wintypes.DWORD),
            ('cy', wintypes.DWORD), ('chars_x', wintypes.DWORD), ('chars_y', wintypes.DWORD),
            ('fill', wintypes.DWORD), ('flags', wintypes.DWORD), ('show', wintypes.WORD),
            ('reserved2_size', wintypes.WORD), ('reserved2', ctypes.c_void_p),
            ('stdin', wintypes.HANDLE), ('stdout', wintypes.HANDLE), ('stderr', wintypes.HANDLE)]
    class ProcessInfo(ctypes.Structure):
        _fields_ = [('process', wintypes.HANDLE), ('thread', wintypes.HANDLE), ('pid', wintypes.DWORD), ('tid', wintypes.DWORD)]
    startup, info = Startup(), ProcessInfo()
    startup.cb = ctypes.sizeof(startup)
    startup.desktop = 'winsta0\\default'
    block = ctypes.create_unicode_buffer('\0'.join(f'{key}={value}' for key, value in sorted(environment.items())) + '\0\0')
    command = ctypes.create_unicode_buffer(command_line)
    api = ctypes.WinDLL('advapi32', use_last_error=True)
    api.CreateProcessWithTokenW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPCWSTR,
        wintypes.LPWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
        ctypes.POINTER(Startup), ctypes.POINTER(ProcessInfo)]
    api.CreateProcessWithTokenW.restype = wintypes.BOOL
    if not api.CreateProcessWithTokenW(int(token), 1, str(executable), command, 0x400 | 0x08000000,
            block, str(executable.parent), ctypes.byref(startup), ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle(info.process)
    kernel.CloseHandle(info.thread)
    return info.pid
