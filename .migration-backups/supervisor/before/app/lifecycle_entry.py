"""Small standalone helper entry; no biometric or regular agent UI imports."""
import argparse
import getpass
import sys


def activation_status(token=None):
    from api.client import get_default_client
    from core.cert import load_cert
    from core.config import DEVICE_UUID
    from services.setup_enrollment import SetupEnrollment
    from platform_adapters.windows.lifecycle import ProtectedSetup
    from core.activation import activate_org
    from core.cert import save_cert
    from core.network.errors import BackendResponseError
    client = get_default_client()
    stale = False
    if token and load_cert():
        try:
            result = client.post('/api/agent/install/status/', {'device_uuid': DEVICE_UUID})
        except BackendResponseError as error:
            if error.status_code not in {401, 403}:
                raise
            stale = True
        else:
            if result.get('state') != 'active' or result.get('device_uuid') != DEVICE_UUID:
                raise ValueError('Current backend activation required')
            return result
    # Keep old credentials until a new signed bootstrap enrollment succeeds.
    def activate(token, *, keypair):
        return activate_org(token, force=stale, keypair=keypair)
    enrollment = SetupEnrollment(DEVICE_UUID, ProtectedSetup(), client, activate, save_cert)
    if token:
        enrollment.activate(token)
    elif not load_cert():
        enrollment.recover()
    if not load_cert():
        raise ValueError('Organization token required')
    result = get_default_client().post('/api/agent/install/status/', {'device_uuid': DEVICE_UUID})
    if result.get('state') != 'active' or result.get('device_uuid') != DEVICE_UUID:
        raise ValueError('Current backend activation required')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--broker', choices=['install', 'uninstall'])
    parser.add_argument('--pipe-name')
    parser.add_argument('--parent-pid', type=int)
    parser.add_argument('--install-path')
    parser.add_argument('--target-sid')
    parser.add_argument('--launch-target-user', action='store_true')
    parser.add_argument('--resume-removal', action='store_true')
    parser.add_argument('--stop-agent', action='store_true')
    parser.add_argument('--cleanup-install-cache', action='store_true')
    parser.add_argument('--prepare-native-recovery', action='store_true')
    parser.add_argument('--check-native-recovery', action='store_true')
    parser.add_argument('--refresh-native-recovery', action='store_true')
    parser.add_argument('--retry-native-removal', action='store_true')
    args = parser.parse_args()
    if args.retry_native_removal:
        from platform_adapters.windows.lifecycle import retry_native_removal
        retry_native_removal()
        return 0
    if args.stop_agent or args.cleanup_install_cache or args.prepare_native_recovery or args.check_native_recovery:
        from platform_adapters.windows.lifecycle import stop_installed_agent, cleanup_install_cache, is_elevated
        if not is_elevated():
            raise OSError('Elevated native uninstaller required')
        if args.check_native_recovery:
            from platform_adapters.windows.lifecycle import check_native_recovery
            check_native_recovery(args.install_path, args.target_sid)
        elif args.prepare_native_recovery:
            from platform_adapters.windows.lifecycle import prepare_native_recovery
            prepare_native_recovery(args.install_path, args.target_sid, refresh=args.refresh_native_recovery)
        elif args.stop_agent:
            stop_installed_agent(args.install_path)
        else:
            cleanup_install_cache(args.install_path)
        return 0
    if args.resume_removal:
        from app.installer_removal import run
        return run()
    if not args.broker or not args.pipe_name or not args.parent_pid or not args.install_path:
        raise ValueError('Native lifecycle context required')
    if args.launch_target_user:
        from platform_adapters.windows.lifecycle_pipe import launch_for_installed_user
        arguments = ['--broker', args.broker, '--pipe-name', args.pipe_name,
            '--parent-pid', str(args.parent_pid), '--install-path', args.install_path]
        launch_for_installed_user(sys.executable, arguments, args.target_sid, args.parent_pid, args.pipe_name)
        return 0
    from platform_adapters.windows.lifecycle import ProtectedReceipt, current_sid, cleanup_user_credentials, preserve_recovery_helper, is_elevated
    from platform_adapters.windows.lifecycle_pipe import serve
    from services.lifecycle_broker import LifecycleBroker
    from services.removal import RemovalController
    from core.network.client import BioGuardApiClient
    from core.config import API_BASE, DEVICE_UUID
    if is_elevated():
        raise OSError('Use the intended non-elevated desktop identity')
    store = ProtectedReceipt(args.install_path)
    removal = RemovalController(BioGuardApiClient(API_BASE), DEVICE_UUID, store,
        lambda: cleanup_user_credentials(args.install_path))
    original_begin = removal.begin
    def begin(code):
        preserve_recovery_helper()
        return original_begin(code)
    removal.begin = begin
    broker = LifecycleBroker(args.broker, activation_status, removal, current_sid(), getpass.getuser())
    serve(args.pipe_name, args.parent_pid, broker)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
