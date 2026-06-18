"""Application configuration using pathlib paths."""

from pathlib import Path

from .resource_path import get_app_data_dir, get_resource_path

# === Application Paths ===
APP_DATA_DIR: Path = get_app_data_dir()
RESOURCES_DIR: Path = get_resource_path("resources")
ICONS_DIR: Path = RESOURCES_DIR / "icons"
STYLES_DIR: Path = RESOURCES_DIR / "styles"

# === Database ===
DB_PATH: Path = APP_DATA_DIR / "myrssapp.db"

# === Default Settings ===
DEFAULT_THEME = "light"
DEFAULT_FONT_FAMILY = "Microsoft YaHei"
DEFAULT_FONT_SIZE = 16
DEFAULT_UPDATE_INTERVAL = 3600  # seconds
MAX_ARTICLES_PER_FEED = 200
