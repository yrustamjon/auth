"""User-bound lifecycle persistence and narrowly scoped Windows cleanup."""
import json
import os
from pathlib import Path
import shutil
import tempfile


def current_sid():
    import win32api
    import win32con
    import win32security
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    try:
        return win32security.ConvertSidToStringSid(win32security.GetTokenInformation(token, win32security.TokenUser)[0])
    finally:
        token.Close()


def is_elevated():
    import ctypes
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def recovery_dir():
    return Path(os.environ['LOCALAPPDATA']) / 'ADBioGuardRemoval'


class ProtectedReceipt:
    def __init__(self, install_path=None):
        self.directory = recovery_dir()
        self.path = self.directory / 'removal.dpapi'
        self.install_path = str(Path(install_path).resolve()) if install_path else None

    def save(self, receipt):
        from storage.legacy_windows_cert import _dpapi_encrypt, _dpapi_decrypt
        data = {**receipt, 'target_sid': current_sid()}
        if self.install_path:
            data['install_path'] = self.install_path
        elif self.path.exists():
            previous = self.load()
            if previous.get('install_path'):
                data['install_path'] = previous['install_path']
        raw = json.dumps(data).encode()
        blob = _dpapi_encrypt(raw)
        if not blob or _dpapi_decrypt(blob) != raw:
            raise OSError('Protected removal persistence unavailable')
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.directory, prefix='.receipt-')
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(blob)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def load(self):
        from storage.legacy_windows_cert import _dpapi_decrypt
        if not self.path.exists():
            return None
        raw = _dpapi_decrypt(self.path.read_bytes())
        if not raw:
            raise OSError('Protected removal receipt could not be read')
        result = json.loads(raw)
        if result.get('target_sid') != current_sid():
            raise OSError('Removal must run as the installed desktop user')
        return result

    def clear(self):
        self.path.unlink(missing_ok=True)


class ProtectedSetup(ProtectedReceipt):
    def __init__(self):
        self.directory = Path(os.environ['LOCALAPPDATA']) / 'ADBioGuardSetup'
        self.path = self.directory / 'activation.dpapi'
        self.install_path = None


def preserve_recovery_helper():
    import sys
    if not getattr(sys, 'frozen', False):
        return  # Development tests do not install executable recovery helpers.
    folder = recovery_dir()
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / 'BioGuardLifecycle.exe'
    if Path(sys.executable).resolve() != destination.resolve():
        shutil.copy2(sys.executable, destination)


def validate_install_path(path):
    original = Path(path)
    if original.exists() and (original.is_symlink() or (original.stat().st_file_attributes & 0x400)):
        raise ValueError('Reparse-point installation directory refused')
    candidate = original.resolve()
    program_files = Path(os.environ.get('ProgramFiles', r'C:\Program Files')).resolve()
    if candidate.name != 'AD BioGuard' or not candidate.is_relative_to(program_files):
        raise ValueError('Unexpected installation directory; cleanup refused')
    return candidate


def cleanup_user_credentials(install_path):
    root = validate_install_path(install_path)
    # Native uninstaller removes binaries before reporting completion. Its own
    # currently-running unins*.exe/dat/msg are the only allowed leftovers.
    if root.exists():
        leftovers = [item for item in root.iterdir() if not (
            item.is_file() and item.name.startswith('unins') and item.suffix.lower() in {'.exe', '.dat', '.msg'})]
        if leftovers:
            raise OSError('Application files remain; finish native removal before retrying')
    expected = [Path(os.environ['APPDATA']) / 'ADBioGuard',
        Path(os.environ['LOCALAPPDATA']) / 'AD BioGuard',
        Path(os.environ['LOCALAPPDATA']) / 'ADBioGuardSetup']
    for directory in expected:
        if directory.exists():
            if directory.is_symlink() or (directory.stat().st_file_attributes & 0x400):
                raise OSError('Credential directory is a reparse point; cleanup refused')
            shutil.rmtree(directory)


def native_recovery_generation():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\AD BioGuard', 0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            return winreg.QueryValueEx(key, 'RecoveryGeneration')[0]
    except FileNotFoundError:
        return None


def store_native_recovery_generation(generation):
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\AD BioGuard', 0,
            winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY) as key:
        winreg.SetValueEx(key, 'RecoveryGeneration', 0, winreg.REG_SZ, generation)


def recovery_file_digest(path):
    import hashlib
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def native_recovery_matches(folder, root, target_sid, generation):
    import re
    if not generation:
        return False
    try:
        for directory in (folder.parent, folder):
            if directory.is_symlink() or directory.stat().st_file_attributes & 0x400:
                return False
        manifest = folder / 'recovery.json'
        if manifest.is_symlink() or manifest.stat().st_file_attributes & 0x400 or manifest.stat().st_size > 65536:
            return False
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if (data.get('generation') != generation or data.get('target_sid') != target_sid
                or data.get('install_path') != str(root)):
            return False
        files = data.get('files', {})
        if 'BioGuardLifecycle.exe' not in files:
            return False
        if not any(name.endswith('.exe') and name.startswith('unins')
                and name[:-4] + '.dat' in files for name in files):
            return False
        for name, digest in files.items():
            if name != 'BioGuardLifecycle.exe' and not re.fullmatch(r'unins[0-9]+\.(exe|dat|msg)', name):
                return False
            item = folder / name
            if item.is_symlink() or item.stat().st_file_attributes & 0x400 or recovery_file_digest(item) != digest:
                return False
        return True
    except (OSError, ValueError, TypeError, AttributeError):
        return False


def check_native_recovery(install_path, target_sid):
    root = validate_install_path(install_path)
    folder = Path(os.environ['ProgramData']) / 'AD BioGuard' / 'native-removal'
    if not native_recovery_matches(folder, root, target_sid, native_recovery_generation()):
        raise OSError('Close the uninstaller and prepare native recovery before retrying')


def prepare_native_recovery(install_path, target_sid, *, refresh=False):
    """Retain the native uninstall log and helper before Inno deletes app files."""
    import re
    import sys
    import win32security
    if not is_elevated() or not re.fullmatch(r'S-1-5-[0-9-]+', target_sid or ''):
        raise OSError('Native recovery requires admin and installed identity')
    root = validate_install_path(install_path)
    folder = Path(os.environ['ProgramData']) / 'AD BioGuard' / 'native-removal'
    for parent in (folder.parent, folder):
        if parent.exists() and (parent.is_symlink() or parent.stat().st_file_attributes & 0x400):
            raise OSError('Native recovery reparse point refused')
        parent.mkdir(exist_ok=True)
        descriptor = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(
            f'D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FRFX;;;{target_sid})',
            win32security.SDDL_REVISION_1)
        win32security.SetFileSecurity(str(parent), win32security.DACL_SECURITY_INFORMATION, descriptor)
    generation = native_recovery_generation()
    if not refresh and native_recovery_matches(folder, root, target_sid, generation):
        return  # Inno holds the source DAT exclusively; use the verified snapshot.
    helper = folder / 'BioGuardLifecycle.exe'
    if Path(sys.executable).resolve() != helper.resolve():
        shutil.copy2(sys.executable, helper)
    sources = list(root.glob('unins*')) if root.exists() else []
    for item in sources:
        if item.is_file() and item.suffix.lower() in {'.exe', '.dat', '.msg'}:
            shutil.copy2(item, folder / item.name)
    if not list(folder.glob('unins*.exe')) or not list(folder.glob('unins*.dat')):
        raise OSError('Native uninstall recovery files unavailable')
    import uuid
    generation = generation or str(uuid.uuid4())
    files = {item.name: recovery_file_digest(item) for item in folder.iterdir()
        if item.is_file() and (item.name == 'BioGuardLifecycle.exe' or (
            item.name.startswith('unins') and item.suffix.lower() in {'.exe', '.dat', '.msg'}))}
    data = {'generation': generation, 'install_path': str(root), 'target_sid': target_sid, 'files': files}
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=folder, delete=False) as temporary:
        json.dump(data, temporary)
        temporary_path = temporary.name
    os.replace(temporary_path, folder / 'recovery.json')
    for name in [*files, 'recovery.json']:
        win32security.SetFileSecurity(str(folder / name), win32security.DACL_SECURITY_INFORMATION, descriptor)
    store_native_recovery_generation(generation)
    check_native_recovery(install_path, target_sid)


def retry_native_removal():
    """Run a disposable copy so the trusted recovery master survives self-delete."""
    import subprocess
    import uuid
    if not is_elevated():
        raise OSError('Run native recovery as administrator')
    master = Path(os.environ['ProgramData']) / 'AD BioGuard' / 'native-removal'
    if master.is_symlink() or master.stat().st_file_attributes & 0x400:
        raise OSError('Native recovery reparse point refused')
    staging = master / str(uuid.uuid4())
    staging.mkdir()
    for item in master.iterdir():
        if item.is_file() and item.name.startswith('unins') and item.suffix.lower() in {'.exe', '.dat', '.msg'}:
            shutil.copy2(item, staging / item.name)
    executable = next(staging.glob('unins*.exe'), None)
    if executable is None:
        raise OSError('Native recovery uninstaller unavailable')
    subprocess.Popen([str(executable)], creationflags=subprocess.CREATE_NO_WINDOW)


def stop_installed_agent(install_path):
    import win32api
    import win32con
    import win32process
    expected = (validate_install_path(install_path) / 'BioGuard.exe').resolve()
    for pid in win32process.EnumProcesses():
        if not pid or pid == os.getpid():
            continue
        handle = None
        matched = False
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION | win32con.PROCESS_TERMINATE, False, pid)
            from .lifecycle_pipe import process_image_path
            executable = process_image_path(handle)
            if Path(executable).resolve() == expected:
                matched = True
                win32api.TerminateProcess(handle, 0)
        except Exception:
            if matched:
                raise OSError('The installed agent could not be stopped') from None
            # Other processes are neither our responsibility nor our authority.
            continue
        finally:
            if handle:
                handle.Close()


def cleanup_install_cache(install_path):
    root = validate_install_path(install_path)
    directory = root / '.webview_data'
    if directory.exists():
        if directory.is_symlink() or (directory.stat().st_file_attributes & 0x400):
            raise OSError('Reparse-point cache refused')
        shutil.rmtree(directory)
