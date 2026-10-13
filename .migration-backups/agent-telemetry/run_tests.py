import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
sys.path[:0]=[str(root/'stage'),str(root.parents[2]/'agent')]
suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_telemetry_outbox')
raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
