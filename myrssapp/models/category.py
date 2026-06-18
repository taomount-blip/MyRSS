"""Category data model (dataclass, no Qt imports)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Category:
    """Represents a feed category / group."""

    id: Optional[int] = None
    name: str = ""
    description: str = ""
    icon: str = ""
    sort_order: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Transient
    feed_count: int = 0
    unread_count: int = 0
