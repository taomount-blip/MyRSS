"""PyInstaller resource path resolution.

In development: resources live alongside the package.
In PyInstaller bundle: resources live under sys._MEIPASS.
"""

import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Return absolute path to a resource, handling both dev and frozen modes."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent.parent
    return base / relative_path


def get_app_data_dir() -> Path:
    """Return the application data directory for storing the database, logs, etc."""
    base = Path.home() / ".myrssapp"
    base.mkdir(parents=True, exist_ok=True)
    return base
