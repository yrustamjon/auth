"""Standalone service executable; importing this module starts nothing."""
import sys


def main():
    if sys.platform != 'win32':
        raise RuntimeError('Windows service only')
    from platform_adapters.windows.service_host import BioGuardService, main as cli
    if len(sys.argv) > 1:
        return cli(sys.argv[1:])
    import servicemanager
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(BioGuardService)
    servicemanager.StartServiceCtrlDispatcher()


if __name__ == '__main__':
    main()
