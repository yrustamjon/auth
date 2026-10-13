import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
if '--actual' in sys.argv:
    sys.argv.remove('--actual')
    sys.path.insert(0,str(root.parents[2]/'agent'))
else:
    sys.path[:0]=[str(root/'stage'),str(root.parents[2]/'agent')]
suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:] or ['tests.test_uninstall_resume_flow','tests.test_removal','tests.test_lifecycle_broker','tests.test_installer_removal'])
raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
