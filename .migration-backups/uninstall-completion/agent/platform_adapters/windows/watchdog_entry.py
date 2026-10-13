"""User-context watchdog: signed server policy, bounded retries, visible removal."""
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path


def main():
    import win32api
    import win32event
    import winerror
    from platform_adapters.windows.lifecycle import validate_install_path
    from platform_adapters.windows.lifecycle_pipe import process_session
    from platform_adapters.windows.supervisor_process import find_process
    from services.supervision import Supervisor
    from services.telemetry import EventOutbox,Reporter
    from api.client import get_default_client
    from core.config import DEVICE_UUID
    from core.cert import is_activated
    from core.network.errors import BackendResponseError
    if not getattr(sys,'frozen',False):raise OSError('Run the installed watchdog executable')
    root=validate_install_path(Path(sys.executable).parent)
    mutex=win32event.CreateMutex(None,True,'Local\\ADBioGuardWatchdogMutex')
    if win32api.GetLastError()==winerror.ERROR_ALREADY_EXISTS:
        mutex.Close()
        return 0
    folder=Path(os.environ['APPDATA'])/'ADBioGuard'
    queue=EventOutbox(folder/'watchdog-events.sqlite3')
    journal=EventOutbox(folder/'telemetry.sqlite3')
    client=get_default_client()
    reporter=Reporter(queue,lambda payload:client.post('/api/agent/telemetry/',{'device_uuid':DEVICE_UUID,'reporter':'supervisor',**payload},timeout=3))
    queue.add('watchdog_started',{'pid':os.getpid()});reporter.start()
    executable=root/'BioGuard.exe';session_id=process_session(os.getpid())
    class Child:
        def __init__(self):
            self.child=subprocess.Popen([str(executable)],cwd=str(root),creationflags=subprocess.CREATE_NO_WINDOW)
            self.pid=self.child.pid
        def poll(self):return self.child.poll()
        def close(self):pass
    guard=Supervisor(lambda:find_process(executable,session_id),Child,queue.add,journal.last_process)
    policy_path=folder/'supervisor-policy.json'
    policy={'allowed':bool(is_activated()),'pause_until':None}
    try:
        saved=json.loads(policy_path.read_text(encoding='utf-8'))
        if isinstance(saved,dict) and type(saved.get('allowed')) is bool:policy=saved
    except (OSError,ValueError):pass
    deadline=0
    try:
        while True:
            now=time.monotonic()
            retry_needed=not guard.explicit_exit and now>=guard.next_start and (guard.process is None or guard.process.poll() is not None)
            if now>=deadline or retry_needed:
                deadline=now+15
                try:
                    result=client.get('/api/agent/supervision/',timeout=3)
                    if not isinstance(result,dict) or type(result.get('allowed')) is not bool:raise ValueError('Invalid supervision policy')
                    policy={'allowed':result['allowed'],'pause_until':result.get('pause_until')}
                    temp=policy_path.with_suffix('.tmp');temp.write_text(json.dumps(policy),encoding='utf-8');os.replace(temp,policy_path)
                except BackendResponseError as error:
                    if error.status_code in (401,403):policy['allowed']=False
                except Exception as error:logging.warning('Supervisor policy deferred (%s)',type(error).__name__)
            paused=False
            if policy.get('pause_until'):
                try:paused=datetime.fromisoformat(policy['pause_until'])>datetime.now(timezone.utc)
                except (ValueError,TypeError):paused=True
            guard.tick(now,allowed=policy['allowed'],paused=paused)
            time.sleep(2)
    finally:
        queue.add('watchdog_exited',{'pid':os.getpid()});reporter.stop()
        if guard.process:guard.process.close()
        mutex.Close()


if __name__=='__main__':raise SystemExit(main())
