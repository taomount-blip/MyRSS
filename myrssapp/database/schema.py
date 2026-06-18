"""Database schema DDL and migration logic."""

import sqlite3

SCHEMA_VERSION = 1

CREATE_TABLES_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Feed categories / groups
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    icon        TEXT DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- RSS subscription feeds
CREATE TABLE IF NOT EXISTS feeds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER DEFAULT NULL,
    title           TEXT NOT NULL,
    url             TEXT NOT NULL UNIQUE,
    site_url        TEXT DEFAULT '',
    description     TEXT DEFAULT '',
    icon_path       TEXT DEFAULT '',
    update_interval INTEGER NOT NULL DEFAULT 3600,
    last_fetched_at TEXT DEFAULT NULL,
    error_count     INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT DEFAULT '',
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_feeds_category ON feeds(category_id);
CREATE INDEX IF NOT EXISTS idx_feeds_active ON feeds(is_active);

-- Articles
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id         INTEGER NOT NULL,
    guid            TEXT NOT NULL,
    title           TEXT NOT NULL DEFAULT '',
    link            TEXT NOT NULL DEFAULT '',
    author          TEXT DEFAULT '',
    summary         TEXT DEFAULT '',
    content         TEXT DEFAULT '',
    published_at    TEXT DEFAULT NULL,
    fetched_at      TEXT NOT NULL DEFAULT (datetime('now')),
    is_read         INTEGER NOT NULL DEFAULT 0,
    is_favorited    INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_guid ON articles(feed_id, guid);
CREATE INDEX IF NOT EXISTS idx_articles_feed ON articles(feed_id);
CREATE INDEX IF NOT EXISTS idx_articles_read ON articles(is_read);
CREATE INDEX IF NOT EXISTS idx_articles_favorited ON articles(is_favorited);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);

-- FTS5 full-text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    title,
    content,
    summary,
    content='articles',
    content_rowid='id'
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
    INSERT INTO articles_fts(rowid, title, content, summary)
    VALUES (new.id, new.title, new.content, new.summary);
END;

CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, title, content, summary)
    VALUES ('delete', old.id, old.title, old.content, old.summary);
END;

CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, title, content, summary)
    VALUES ('delete', old.id, old.title, old.content, old.summary);
    INSERT INTO articles_fts(rowid, title, content, summary)
    VALUES (new.id, new.title, new.content, new.summary);
END;

-- Tags
CREATE TABLE IF NOT EXISTS tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    color       TEXT DEFAULT '#3498db',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Article-tag many-to-many
CREATE TABLE IF NOT EXISTS article_tags (
    article_id  INTEGER NOT NULL,
    tag_id      INTEGER NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (article_id, tag_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Translation cache
CREATE TABLE IF NOT EXISTS translation_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_hash     TEXT NOT NULL,
    source_text     TEXT NOT NULL,
    source_lang     TEXT NOT NULL,
    target_lang     TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_translation_cache_hash ON translation_cache(source_hash);

-- Application settings (key-value)
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

DEFAULT_SETTINGS_SQL = """
INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'light');
INSERT OR IGNORE INTO settings (key, value) VALUES ('font_family', 'Microsoft YaHei');
INSERT OR IGNORE INTO settings (key, value) VALUES ('font_size', '16');
INSERT OR IGNORE INTO settings (key, value) VALUES ('update_interval', '3600');
INSERT OR IGNORE INTO settings (key, value) VALUES ('max_articles_per_feed', '200');
INSERT OR IGNORE INTO settings (key, value) VALUES ('translation_api_url', 'https://api.hunyuan.cloud.tencent.com/v1');
INSERT OR IGNORE INTO settings (key, value) VALUES ('translation_api_key', '');
INSERT OR IGNORE INTO settings (key, value) VALUES ('translation_model', 'hunyuan-lite');
"""


def initialize_database(conn: sqlite3.Connection) -> None:
    """Create all tables, indexes, triggers, and default data."""
    conn.executescript(CREATE_TABLES_SQL)
    conn.executescript(DEFAULT_SETTINGS_SQL)

    # Record schema version
    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION,),
    )
    conn.commit()


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Return the current schema version, or 0 if not initialized."""
    try:
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        return row["version"] if row else 0
    except sqlite3.OperationalError:
        return 0
