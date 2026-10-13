"""SCM host. Deliberately separate from the interactive pre-release GUI."""
import secrets
import threading
import win32service
import win32serviceutil

from services.authorization import SessionAuthority


def make_server():
    from platform_adapters.windows.local_pipe import NamedPipeServer
    return NamedPipeServer()


class BioGuardService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'BioGuardAuthority'
    _svc_display_name_ = 'BioGuard Authority (VM test)'
    _svc_description_ = 'Session-bound MFA authority foundation; VM testing only.'

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = threading.Event()
        self.authority = SessionAuthority(secrets.token_hex(32))

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_event.set()

    def SvcShutdown(self):
        self.SvcStop()

    def SvcDoRun(self):
        try:
            make_server().serve(self.stop_event, self.authority)
        finally:
            self.stop_event.set()


def main(argv=None):
    from platform_adapters.windows.service_security import service_cli
    return service_cli(BioGuardService, argv)
