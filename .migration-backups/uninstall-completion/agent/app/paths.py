"""Resolve assets in source checkouts and PyInstaller bundles."""
from pathlib import Path
import sys


def application_root() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    return Path(bundle_root) if bundle_root else Path(__file__).resolve().parents[1]
