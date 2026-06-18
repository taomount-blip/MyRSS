"""MyRssApp entry point. Launches the QApplication and main window."""

import sys
from pathlib import Path

# Ensure the myrssapp package is importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from myrssapp.database.connection import DatabaseConnection
from myrssapp.database.schema import initialize_database, get_schema_version
from myrssapp.services.feed_service import FeedService
from myrssapp.services.article_service import ArticleService
from myrssapp.services.fetch_service import FetchService
from myrssapp.services.translation_service import TranslationService
from myrssapp.services.settings_service import SettingsService
from myrssapp.viewmodels.main_viewmodel import MainViewModel
from myrssapp.utils.config import ICONS_DIR, DB_PATH, STYLES_DIR
from myrssapp.utils.theme_manager import ThemeManager
from myrssapp.views.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("MyRssApp")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MyRssApp")

    # App icon
    icon_path = ICONS_DIR / "app.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Initialize database
    db = DatabaseConnection(DB_PATH)
    conn = db.get_connection()
    schema_ver = get_schema_version(conn)
    if schema_ver == 0:
        initialize_database(conn)
    elif schema_ver < 1:
        initialize_database(conn)

    # Create service layer
    feed_service = FeedService(db)
    article_service = ArticleService(db)
    fetch_service = FetchService(db)
    translation_service = TranslationService(db)
    settings_service = SettingsService(db)

    # Create main ViewModel (wires all child VMs)
    main_vm = MainViewModel(
        feed_service=feed_service,
        article_service=article_service,
        fetch_service=fetch_service,
        translation_service=translation_service,
        settings_service=settings_service,
    )

    # Theme
    theme_manager = ThemeManager(STYLES_DIR)
    theme_manager.load_base()
    theme_manager.apply_theme(settings_service.theme)

    # Create and show MainWindow
    window = MainWindow(main_vm)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
