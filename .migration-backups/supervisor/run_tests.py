import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
names=sys.argv[1:]
actual='--actual' in names
if actual:names.remove('--actual')
sys.path[:0]=([str(root/'stage')] if not actual else [])+[str(root.parents[2]/'agent')]
suite=unittest.defaultTestLoader.loadTestsFromNames(names or ['tests.test_supervision'])
raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
