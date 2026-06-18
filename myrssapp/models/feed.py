"""Feed data model (dataclass, no Qt imports)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Feed:
    """Represents an RSS subscription feed."""

    id: Optional[int] = None
    category_id: Optional[int] = None
    title: str = ""
    url: str = ""
    site_url: str = ""
    description: str = ""
    icon_path: str = ""
    update_interval: int = 3600  # seconds
    last_fetched_at: Optional[str] = None
    error_count: int = 0
    last_error: str = ""
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Transient fields (not in DB)
    unread_count: int = 0
    total_count: int = 0
