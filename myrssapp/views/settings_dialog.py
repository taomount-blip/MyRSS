"""Settings dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QComboBox, QSpinBox, QLineEdit, QPushButton,
    QLabel, QMessageBox,
)
from PySide6.QtCore import Qt

from ..viewmodels.settings_viewmodel import SettingsViewModel


class SettingsDialog(QDialog):
    """Application settings dialog with tabs."""

    def __init__(self, viewmodel: SettingsViewModel, parent=None):
        super().__init__(parent)
        self._vm = viewmodel
        self.setWindowTitle("设置")
        self.resize(450, 400)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # Appearance tab
        appearance = self._create_appearance_tab()
        tabs.addTab(appearance, "外观")

        # Sync tab
        sync = self._create_sync_tab()
        tabs.addTab(sync, "同步")

        # Translation tab
        translation = self._create_translation_tab()
        tabs.addTab(translation, "翻译")

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)

        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self._on_apply)
        apply_btn.setDefault(True)
        btn_layout.addWidget(apply_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        self._vm.settings_applied.connect(
            lambda: QMessageBox.information(self, "设置", "设置已保存")
        )

    def _create_appearance_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["light", "dark"])
        idx = self._theme_combo.findText(self._vm.theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        form.addRow("主题:", self._theme_combo)

        self._font_family_input = QLineEdit(self._vm.font_family)
        form.addRow("字体:", self._font_family_input)

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(10, 48)
        self._font_size_spin.setValue(self._vm.font_size)
        form.addRow("字号:", self._font_size_spin)

        return w

    def _create_sync_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(60, 86400)
        self._interval_spin.setSuffix(" 秒")
        self._interval_spin.setValue(self._vm.update_interval)
        form.addRow("自动更新间隔:", self._interval_spin)

        return w

    def _create_translation_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._api_url_input = QLineEdit(self._vm.translation_api_url)
        self._api_url_input.setPlaceholderText("https://api.hunyuan.cloud.tencent.com/v1")
        form.addRow("API 地址:", self._api_url_input)

        self._api_key_input = QLineEdit(self._vm.translation_api_key)
        self._api_key_input.setEchoMode(QLineEdit.Password)
        self._api_key_input.setPlaceholderText("输入 API Key")
        form.addRow("API Key:", self._api_key_input)

        self._model_input = QLineEdit(self._vm.translation_model)
        self._model_input.setPlaceholderText("hunyuan-lite / hunyuan-pro / hy3-preview")
        form.addRow("模型:", self._model_input)

        form.addRow(QLabel("支持所有 OpenAI 兼容 API"))

        return w

    def _on_apply(self) -> None:
        self._vm.theme = self._theme_combo.currentText()
        self._vm.font_family = self._font_family_input.text()
        self._vm.font_size = self._font_size_spin.value()
        self._vm.update_interval = self._interval_spin.value()
        self._vm.translation_api_url = self._api_url_input.text()
        self._vm.translation_api_key = self._api_key_input.text()
        self._vm.translation_model = self._model_input.text()
        self._vm.apply()

    def _on_reset(self) -> None:
        self._vm.reset_defaults()
        self._theme_combo.setCurrentText(self._vm.theme)
        self._font_family_input.setText(self._vm.font_family)
        self._font_size_spin.setValue(self._vm.font_size)
        self._interval_spin.setValue(self._vm.update_interval)
