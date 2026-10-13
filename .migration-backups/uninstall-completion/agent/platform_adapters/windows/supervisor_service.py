"""Standard, administrator-manageable SCM supervisor; not PPL or native login MFA."""
import re
import subprocess
import sys
import threading
from pathlib import Path
import win32service
import win32serviceutil

NAME='BioGuardSupervisor'


def installed_context():
    import winreg
    import win32com.shell.shell as shell
    import win32com.shell.shellcon as shellcon
    expected=Path(shell.SHGetFolderPath(0,shellcon.CSIDL_PROGRAM_FILES,None,0))/'AD BioGuard'
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\AD BioGuard',0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
        root=Path(winreg.QueryValueEx(key,'InstallPath')[0]);sid=winreg.QueryValueEx(key,'TargetUserSID')[0]
    if root.resolve()!=expected.resolve() or not re.fullmatch(r'S-1-5-[0-9-]+',sid):raise OSError('Invalid installed context')
    for path in [root,*root.parents,root/'BioGuardWatchdog.exe',root/'BioGuard.exe',root/'BioGuardSupervisor.exe']:
        if path.stat().st_file_attributes&0x400:raise OSError('Reparse-point supervision refused')
    if Path(sys.executable).resolve()!= (root/'BioGuardSupervisor.exe').resolve():raise OSError('Unexpected service executable')
    return root,sid


def target_sessions(target_sid):
    import win32ts,win32security
    result=[]
    for item in win32ts.WTSEnumerateSessions():
        if item['State']!=win32ts.WTSActive or item['SessionId']==0:continue
        token=None
        try:
            token=win32ts.WTSQueryUserToken(item['SessionId'])
            sid=win32security.ConvertSidToStringSid(win32security.GetTokenInformation(token,win32security.TokenUser)[0])
            if sid==target_sid:result.append(item['SessionId'])
        except Exception:continue
        finally:
            if token:token.Close()
    return result


def launch_watchdog(root,session_id):
    import win32ts,win32profile,win32process,win32con
    from platform_adapters.windows.supervisor_process import ProcessRef
    token=win32ts.WTSQueryUserToken(session_id)
    try:
        env=win32profile.CreateEnvironmentBlock(token,False)
        startup=win32process.STARTUPINFO();startup.lpDesktop='winsta0\\default'
        executable=root/'BioGuardWatchdog.exe'
        process,thread,pid,_=win32process.CreateProcessAsUser(token,str(executable),subprocess.list2cmdline([str(executable)]),
            None,None,False,win32con.CREATE_UNICODE_ENVIRONMENT|win32con.CREATE_NO_WINDOW,env,str(root),startup)
        thread.Close()
        return ProcessRef(process,pid)
    finally:token.Close()


class BioGuardSupervisor(win32serviceutil.ServiceFramework):
    _svc_name_=NAME
    _svc_display_name_='ADAuth Agent Supervisor'
    _svc_description_='Restarts the installed agent after unexpected exits. Administrators can stop or remove this service.'
    def __init__(self,args):
        super().__init__(args);self.stopping=threading.Event()
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING);self.stopping.set()
    def SvcShutdown(self):self.SvcStop()
    def SvcDoRun(self):
        import servicemanager
        from platform_adapters.windows.supervisor_process import find_process
        children={}
        try:
            root,sid=installed_context()
            while not self.stopping.is_set():
                sessions=target_sessions(sid)
                for session in sessions:
                    child=children.get(session)
                    if child and child.poll() is None:continue
                    if child:children.pop(session).close()
                    try:children[session]=find_process(root/'BioGuardWatchdog.exe',session,terminate_access=True) or launch_watchdog(root,session)
                    except Exception as error:servicemanager.LogErrorMsg('ADAuth supervisor launch failed: '+type(error).__name__)
                for session in list(children):
                    if session not in sessions:children.pop(session).close()
                self.stopping.wait(5)
        finally:
            for child in children.values():
                try:child.terminate()
                except Exception as error:servicemanager.LogErrorMsg('ADAuth watchdog stop failed: '+type(error).__name__)
                finally:child.close()


def cli(command):
    import ctypes
    import win32security
    if command not in {'install','start','stop','remove','status'}:raise ValueError('Unsupported service operation')
    if command=='status':print(win32serviceutil.QueryServiceStatus(NAME));return
    if not ctypes.windll.shell32.IsUserAnAdmin():raise OSError('Administrator permission required')
    if command in {'install','start'}:installed_context()
    if command=='install':
        if not getattr(sys,'frozen',False):raise OSError('Install the frozen supervisor executable')
        try:win32serviceutil.QueryServiceStatus(NAME)
        except Exception:
            win32serviceutil.InstallService('platform_adapters.windows.supervisor_service.BioGuardSupervisor',NAME,
                BioGuardSupervisor._svc_display_name_,exeName=sys.executable,
                description=BioGuardSupervisor._svc_description_,startType=win32service.SERVICE_DEMAND_START)
        manager=win32service.OpenSCManager(None,None,win32service.SC_MANAGER_CONNECT)
        handle=None
        try:
            handle=win32service.OpenService(manager,NAME,win32service.SERVICE_ALL_ACCESS)
            descriptor=win32security.ConvertStringSecurityDescriptorToSecurityDescriptor('D:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;LC;;;IU)',1)
            win32service.SetServiceObjectSecurity(handle,win32security.DACL_SECURITY_INFORMATION,descriptor)
            win32service.ChangeServiceConfig2(handle,win32service.SERVICE_CONFIG_FAILURE_ACTIONS,{'ResetPeriod':86400,'RebootMsg':None,'Command':None,
                'Actions':[(win32service.SC_ACTION_RESTART,5000),(win32service.SC_ACTION_RESTART,30000),(win32service.SC_ACTION_RESTART,60000)]})
            win32service.ChangeServiceConfig2(handle,win32service.SERVICE_CONFIG_FAILURE_ACTIONS_FLAG,True)
            win32service.ChangeServiceConfig(handle,win32service.SERVICE_NO_CHANGE,win32service.SERVICE_AUTO_START,
                win32service.SERVICE_NO_CHANGE,None,None,0,None,None,None,None)
        finally:
            if handle:win32service.CloseServiceHandle(handle)
            win32service.CloseServiceHandle(manager)
        if win32serviceutil.QueryServiceStatus(NAME)[1]!=win32service.SERVICE_RUNNING:win32serviceutil.StartService(NAME)
    elif command=='start':win32serviceutil.StartService(NAME)
    else:
        try:
            status=win32serviceutil.QueryServiceStatus(NAME)[1]
            if status!=win32service.SERVICE_STOPPED:
                win32serviceutil.StopService(NAME)
                win32serviceutil.WaitForServiceStatus(NAME,win32service.SERVICE_STOPPED,30)
        except Exception as error:
            if getattr(error,'winerror',None)!=1060:raise
        if command=='remove':
            try:win32serviceutil.RemoveService(NAME)
            except Exception as error:
                if getattr(error,'winerror',None)!=1060:raise


def main():
    if len(sys.argv)>1:cli(sys.argv[1]);return
    import servicemanager
    servicemanager.Initialize();servicemanager.PrepareToHostSingle(BioGuardSupervisor);servicemanager.StartServiceCtrlDispatcher()


if __name__=='__main__':main()
