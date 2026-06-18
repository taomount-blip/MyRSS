"""Settings key-value data model (dataclass, no Qt imports)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SettingsItem:
    """Represents a single key-value setting."""

    key: str = ""
    value: str = ""
    updated_at: str = datetime.now().isoformat()
