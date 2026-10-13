"""Run Django with an installed Python when the local venv executable is stale."""
import os
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
os.chdir(root)
sys.path.insert(0, str(root))
packages = root / 'venv' / 'Lib' / 'site-packages'
if packages.exists():
    sys.path.append(str(packages))
os.environ.setdefault('PUBLIC_SITE_URL', 'http://localhost:8000')
sys.argv[0] = str(root / 'manage.py')
runpy.run_path(str(root / 'manage.py'), run_name='__main__')

