"""Article data model (dataclass, no Qt imports)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    """Represents a single article/entry from an RSS feed."""

    id: Optional[int] = None
    feed_id: int = 0
    guid: str = ""
    title: str = ""
    link: str = ""
    author: str = ""
    summary: str = ""
    content: str = ""
    published_at: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_read: bool = False
    is_favorited: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Transient
    feed_title: str = ""
