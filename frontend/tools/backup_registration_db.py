"""Create a consistent local backup before the additive registration migration."""
from pathlib import Path
from datetime import datetime
import sqlite3

root = Path(__file__).resolve().parents[2]
database = root / 'db.sqlite3'
folder = root / 'frontend' / 'artifacts'
folder.mkdir(exist_ok=True)
target = folder / ('db-before-registration-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3')
with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as source:
    with sqlite3.connect(target) as destination:
        source.backup(destination)
print('Database backup created:', target.name)
