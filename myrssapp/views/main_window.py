"""Main window of MyRssApp – wires all Views to their ViewModels."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QStatusBar, QLabel,
    QWidget, QVBoxLayout, QTabWidget, QMessageBox,
)
from PySide6.QtGui import QAction, QKeySequence

from ..viewmodels.main_viewmodel import MainViewModel
from ..viewmodels.full_translation_viewmodel import FullTranslationViewModel
from .feed_list_view import FeedListView
from .article_list_view import ArticleListView
from .article_detail_view import ArticleDetailView
from .add_feed_dialog import AddFeedDialog
from .settings_dialog import SettingsDialog
from .translation_panel import TranslationPanel
from .full_translation_dialog import FullTranslationDialog
from .widgets.search_bar import SearchBar


class MainWindow(QMainWindow):
    """Top-level window containing the feed sidebar, article list, and reading area."""

    def __init__(self, viewmodel: MainViewModel):
        super().__init__()
        self._vm = viewmodel
        self.setWindowTitle("MyRssApp - RSS Reader")
        self.resize(1200, 800)
        self.setMinimumSize(800, 500)

        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_central_area()

        # VM error handling
        self._vm.error_occurred.connect(self._on_error)

    def _setup_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("文件(&F)")

        add_feed_action = QAction("添加订阅(&A)", self)
        add_feed_action.setShortcut(QKeySequence("Ctrl+N"))
        add_feed_action.triggered.connect(self._open_add_feed_dialog)
        file_menu.addAction(add_feed_action)

        import_opml_action = QAction("导入 OPML(&I)", self)
        import_opml_action.setShortcut(QKeySequence("Ctrl+O"))
        import_opml_action.triggered.connect(self._import_opml)
        file_menu.addAction(import_opml_action)

        export_opml_action = QAction("导出 OPML(&E)", self)
        export_opml_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        export_opml_action.triggered.connect(self._export_opml)
        file_menu.addAction(export_opml_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menu_bar.addMenu("视图(&V)")

        refresh_action = QAction("刷新所有订阅(&R)", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._vm.refresh_all)
        view_menu.addAction(refresh_action)

        toggle_read_action = QAction("切换已读状态(&M)", self)
        toggle_read_action.setShortcut(QKeySequence("Ctrl+M"))
        view_menu.addAction(toggle_read_action)

        view_menu.addSeparator()

        toggle_fav_action = QAction("切换收藏(&F)", self)
        toggle_fav_action.setShortcut(QKeySequence("Ctrl+D"))
        view_menu.addAction(toggle_fav_action)

        # Tools menu
        tools_menu = menu_bar.addMenu("工具(&T)")

        settings_action = QAction("设置(&S)", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._open_settings_dialog)
        tools_menu.addAction(settings_action)

        translate_action = QAction("翻译面板(&T)", self)
        translate_action.setShortcut(QKeySequence("Ctrl+T"))
        translate_action.triggered.connect(self._toggle_translation_panel)
        tools_menu.addAction(translate_action)

        # Help menu
        help_menu = menu_bar.addMenu("帮助(&H)")

        about_action = QAction("关于 MyRssApp(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self) -> None:
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("就绪")
        self._status_bar.addWidget(self._status_label)

        self._vm.sync_status_changed.connect(self._status_label.setText)

    def _setup_central_area(self) -> None:
        """Set up the three-panel splitter layout with real views."""
        splitter = QSplitter(Qt.Horizontal, self)

        # Left: feed list
        self._feed_list = FeedListView(self._vm.feed_list_vm)
        splitter.addWidget(self._feed_list)

        # Center: article list + search bar
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self._search_bar = SearchBar()
        self._search_bar.search_requested.connect(
            self._vm.article_list_vm.search
        )
        self._search_bar.cleared.connect(
            lambda: self._vm.article_list_vm.search("")
        )
        center_layout.addWidget(self._search_bar)

        self._article_list = ArticleListView(self._vm.article_list_vm)
        center_layout.addWidget(self._article_list)

        splitter.addWidget(center_widget)

        # Right: article detail + translation tabs
        self._right_tabs = QTabWidget()
        self._article_detail = ArticleDetailView(self._vm.article_detail_vm)
        self._article_detail.translate_full_requested.connect(self._on_translate_full)
        self._right_tabs.addTab(self._article_detail, "阅读")
        self._translation_panel = TranslationPanel(self._vm.translation_vm)
        self._right_tabs.addTab(self._translation_panel, "翻译")
        splitter.addWidget(self._right_tabs)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 3)

        self.setCentralWidget(splitter)

    # -- Actions --

    def _open_add_feed_dialog(self) -> None:
        dlg = AddFeedDialog(self._vm.add_feed_vm, self)
        dlg.exec_()

    def _open_settings_dialog(self) -> None:
        dlg = SettingsDialog(self._vm.settings_vm, self)
        dlg.exec_()

    def _toggle_translation_panel(self) -> None:
        """Switch right panel to translation tab."""
        self._right_tabs.setCurrentWidget(self._translation_panel)

    def _on_translate_full(self, article) -> None:
        """Open full article translation dialog."""
        ft_vm = FullTranslationViewModel(self._vm._translation_service)
        ft_vm.load_article(article)
        dlg = FullTranslationDialog(ft_vm, self)
        dlg.exec_()

    def _import_opml(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "导入 OPML", "", "OPML 文件 (*.opml *.xml);;所有文件 (*)"
        )
        if path:
            from ..services.opml_service import OPMLService
            svc = OPMLService(self._vm._feed_service._db)
            count = svc.import_opml(path)
            self._vm.feed_list_vm.load_feeds()
            QMessageBox.information(self, "导入完成", f"成功导入 {count} 个订阅源")

    def _export_opml(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 OPML", "myrssapp_subscriptions.opml",
            "OPML 文件 (*.opml);;所有文件 (*)"
        )
        if path:
            from ..services.opml_service import OPMLService
            svc = OPMLService(self._vm._feed_service._db)
            svc.export_opml(path)
            QMessageBox.information(self, "导出完成", f"订阅已导出到: {path}")

    def _show_about(self) -> None:
        QMessageBox.about(
            self, "关于 MyRssApp",
            "<h2>MyRssApp</h2>"
            "<p>Windows 桌面 RSS 阅读器</p>"
            "<p>版本 1.0.0</p>"
            "<p>基于 PySide6 + Python 构建</p>"
        )

    def _on_error(self, message: str) -> None:
        QMessageBox.warning(self, "错误", message)
