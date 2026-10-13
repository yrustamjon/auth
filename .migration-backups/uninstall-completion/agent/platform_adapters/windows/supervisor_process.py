"""Exact-path process handles; never stop processes by a shared executable name."""
import os
from pathlib import Path


class ProcessRef:
    def __init__(self,handle,pid):self.handle,self.pid=handle,pid
    def poll(self):
        import win32event,win32process
        return None if win32event.WaitForSingleObject(self.handle,0)==258 else win32process.GetExitCodeProcess(self.handle)
    def close(self):
        if self.handle:self.handle.Close();self.handle=None
    def terminate(self):
        import win32process,win32event
        if self.poll() is None:
            win32process.TerminateProcess(self.handle,0)
            if win32event.WaitForSingleObject(self.handle,3000)==win32event.WAIT_TIMEOUT:raise OSError('Watchdog did not stop')


def find_process(executable,session_id,*,terminate_access=False):
    import win32api,win32con,win32process
    from .lifecycle_pipe import process_image_path,process_session
    expected=str(Path(executable).resolve()).casefold()
    for pid in win32process.EnumProcesses():
        if pid in (0,os.getpid()):continue
        handle=None
        try:
            if process_session(pid)!=session_id:continue
            access=win32con.PROCESS_QUERY_LIMITED_INFORMATION|win32con.SYNCHRONIZE
            if terminate_access:access|=win32con.PROCESS_TERMINATE
            handle=win32api.OpenProcess(access,False,pid)
            if str(Path(process_image_path(handle)).resolve()).casefold()==expected:
                result=ProcessRef(handle,pid)
                if result.poll() is None:return result
        except Exception:pass
        if handle:handle.Close()
    return None
