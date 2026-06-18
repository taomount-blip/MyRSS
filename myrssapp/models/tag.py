"""Tag data model (dataclass, no Qt imports)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Tag:
    """Represents a tag that can be attached to articles."""

    id: Optional[int] = None
    name: str = ""
    color: str = "#3498db"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ArticleTag:
    """Many-to-many relationship between articles and tags."""

    article_id: int = 0
    tag_id: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
