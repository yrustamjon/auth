"""Local development artifacts only; does not install services or publish releases."""
import os
import subprocess
import sys
from pathlib import Path

base=Path(__file__).resolve().parent
agent=base.parents[2]/'agent'
tooling=base/'tooling'
sys.path[:0]=[str(tooling),str(agent)]
os.environ['PYTHONPATH']=os.pathsep.join([str(tooling),str(agent)])
mode=sys.argv[1]
specs={'watchdog':'bioguard-watchdog.spec','supervisor':'bioguard-supervisor.spec','lifecycle':'bioguard-lifecycle.spec','gui':'bioguard.spec'}
if mode in specs:
    from PyInstaller.__main__ import run
    spec=agent/'builders/windows'/specs[mode]
    if mode=='gui' and not (agent/'icon.ico').exists():
        text=spec.read_text(encoding='utf-8').replace('PROJECT_ROOT = Path(SPECPATH).resolve().parents[1]',f'PROJECT_ROOT = Path({str(agent)!r})')
        text=text.replace("icon=str(PROJECT_ROOT / 'icon.ico')",'icon=None')
        spec=base/'gui-local.spec';spec.write_text(text,encoding='utf-8')
    run([str(spec),'--noconfirm','--distpath',str(base/'dist'),'--workpath',str(base/'build'/mode)])
elif mode=='installer':
    compiler=agent/'.migration-backups/lifecycle/tools/inno/ISCC.exe'
    text=(agent/'builders/windows/bioguard_installer.iss').read_text(encoding='utf-8')
    text=text.replace('#define MyBuildDir     BioGuardProjectRoot + "\\dist\\BioGuard"',f'#define MyBuildDir "{base / "dist/BioGuard"}"')
    text=text.replace('{#BioGuardProjectRoot}\\dist\\',str(base/'dist')+'\\')
    text=text.replace('OutputDir={#BioGuardProjectRoot}\\installer_output',f'OutputDir={base / "installer"}')
    spec=base/'supervisor-local.iss';spec.write_text(text,encoding='utf-8-sig')
    command=[str(compiler),f'/DBioGuardProjectRoot={agent}','/DMyAppVersion=1.0.3-supervisor-dev',str(spec)]
    raise SystemExit(subprocess.call(command))
else:raise SystemExit('Choose watchdog, supervisor, lifecycle, gui, or installer')
