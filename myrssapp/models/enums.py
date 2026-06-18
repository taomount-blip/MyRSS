"""Enumerations used across the application (no Qt imports)."""

from enum import Enum, auto


class ArticleStatus(Enum):
    UNREAD = auto()
    READ = auto()


class FeedStatus(Enum):
    ACTIVE = auto()
    ERROR = auto()
    DISABLED = auto()


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"


class SortOrder(Enum):
    NEWEST_FIRST = "newest"
    OLDEST_FIRST = "oldest"
