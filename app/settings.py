from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QPushButton, QGroupBox, QFormLayout,
    QMessageBox, QLineEdit, QScrollArea, QFrame, QFileDialog,
    QGridLayout,
)

from src.config import SYNC_SERVICES, ALWAYS_ON_SERVICES, OLLAMA_MODEL, APP_CONFIG_PATH
from src.config import load_service_configs, DEFAULT_SERVICE_CONFIGS
import json


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._svc_editors = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("heading")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(12)

        for svc in SYNC_SERVICES:
            card = self._make_service_card(svc)
            inner_layout.addWidget(card)

        always_group = QGroupBox("Always-On Services")
        always_form = QVBoxLayout()
        for svc in ALWAYS_ON_SERVICES:
            cb = QCheckBox(svc)
            cb.setChecked(True)
            cb.setEnabled(False)
            always_form.addWidget(cb)
        always_group.setLayout(always_form)
        inner_layout.addWidget(always_group)

        ollama_group = QGroupBox("Ollama")
        ollama_form = QFormLayout()
        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        self._model_combo.addItems([
            "qwen2.5:3b",
            "qwen2.5:14b",
            "codellama:7b",
            "llama3.2:3b",
            "llama3.1:8b",
        ])
        idx = self._model_combo.findText(OLLAMA_MODEL)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
        else:
            self._model_combo.setEditText(OLLAMA_MODEL)
        ollama_form.addRow("Model:", self._model_combo)
        ollama_group.setLayout(ollama_form)
        inner_layout.addWidget(ollama_group)

        notif_group = QGroupBox("Notifications")
        notif_form = QVBoxLayout()
        self._notif_failures = QCheckBox("Notify on failures only")
        self._notif_failures.setChecked(True)
        notif_form.addWidget(self._notif_failures)
        self._notif_always = QCheckBox("Notify on every update")
        notif_form.addWidget(self._notif_always)
        notif_group.setLayout(notif_form)
        inner_layout.addWidget(notif_group)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._save_btn = QPushButton("Save Settings")
        self._save_btn.clicked.connect(self._save)
        btn_row.addWidget(self._save_btn)
        layout.addLayout(btn_row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._status_label)

        self._load_settings()

    def _make_service_card(self, svc_name):
        card = QGroupBox(svc_name)
        grid = QGridLayout()
        grid.setSpacing(6)

        row = 0
        grid.addWidget(QLabel("Display name:"), row, 0)
        display_edit = QLineEdit()
        grid.addWidget(display_edit, row, 1, 1, 2)
        row += 1

        enabled_cb = QCheckBox("Enabled")
        enabled_cb.setChecked(True)
        grid.addWidget(enabled_cb, row, 0, 1, 3)
        row += 1

        grid.addWidget(QLabel("Log path:"), row, 0)
        log_edit = QLineEdit()
        log_btn = QPushButton("Browse…")
        log_btn.setFixedWidth(80)
        log_btn.clicked.connect(lambda: self._browse_file(log_edit))
        grid.addWidget(log_edit, row, 1)
        grid.addWidget(log_btn, row, 2)
        row += 1

        grid.addWidget(QLabel("Launch cmd:"), row, 0)
        launch_edit = QLineEdit()
        launch_btn = QPushButton("Browse…")
        launch_btn.setFixedWidth(80)
        launch_btn.clicked.connect(lambda: self._browse_file(launch_edit))
        grid.addWidget(launch_edit, row, 1)
        grid.addWidget(launch_btn, row, 2)
        row += 1

        grid.addWidget(QLabel("Watch dir:"), row, 0)
        watch_edit = QLineEdit()
        watch_btn = QPushButton("Browse…")
        watch_btn.setFixedWidth(80)
        watch_btn.clicked.connect(lambda: self._browse_dir(watch_edit))
        grid.addWidget(watch_edit, row, 1)
        grid.addWidget(watch_btn, row, 2)
        row += 1

        notify_fail_cb = QCheckBox("Notify on failure")
        notify_fail_cb.setChecked(True)
        grid.addWidget(notify_fail_cb, row, 0, 1, 2)
        notify_succ_cb = QCheckBox("Notify on success")
        notify_succ_cb.setChecked(False)
        grid.addWidget(notify_succ_cb, row, 2)
        row += 1

        card.setLayout(grid)
        self._svc_editors[svc_name] = {
            "display_name": display_edit,
            "enabled": enabled_cb,
            "log_path": log_edit,
            "launch_cmd": launch_edit,
            "watch_dir": watch_edit,
            "notify_on_failure": notify_fail_cb,
            "notify_on_success": notify_succ_cb,
        }
        return card

    def _browse_file(self, edit):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select file",
            options=QFileDialog.DontUseNativeDialog)
        if path:
            edit.setText(path)

    def _browse_dir(self, edit):
        path = QFileDialog.getExistingDirectory(
            self, "Select directory",
            options=QFileDialog.DontUseNativeDialog)
        if path:
            edit.setText(path)

    def _load_settings(self):
        cfg = {}
        if APP_CONFIG_PATH.exists():
            try:
                cfg = json.loads(APP_CONFIG_PATH.read_text())
            except Exception:
                pass

        service_overrides = cfg.get("services", {})
        defaults = DEFAULT_SERVICE_CONFIGS

        for svc, editors in self._svc_editors.items():
            merged = dict(defaults.get(svc, {}))
            if svc in service_overrides:
                merged.update(service_overrides[svc])

            editors["display_name"].setText(merged.get("display_name", svc))
            editors["enabled"].setChecked(
                svc not in cfg.get("disabled_services", [])
            )
            editors["log_path"].setText(merged.get("log_path", ""))
            editors["launch_cmd"].setText(merged.get("launch_cmd", ""))
            editors["watch_dir"].setText(merged.get("watch_dir", ""))
            editors["notify_on_failure"].setChecked(merged.get("notify_on_failure", True))
            editors["notify_on_success"].setChecked(merged.get("notify_on_success", False))

        model = cfg.get("ollama_model")
        if model:
            idx = self._model_combo.findText(model)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
            else:
                self._model_combo.setEditText(model)
        notif_mode = cfg.get("notification_mode", "failures")
        self._notif_failures.setChecked(notif_mode == "failures")
        self._notif_always.setChecked(notif_mode == "always")

    def _save(self):
        enabled = []
        disabled = []
        services = {}

        defaults = DEFAULT_SERVICE_CONFIGS

        for svc, editors in self._svc_editors.items():
            merged = dict(defaults.get(svc, {}))
            merged["display_name"] = editors["display_name"].text() or svc
            merged["log_path"] = editors["log_path"].text()
            merged["launch_cmd"] = editors["launch_cmd"].text()
            merged["watch_dir"] = editors["watch_dir"].text()
            merged["notify_on_failure"] = editors["notify_on_failure"].isChecked()
            merged["notify_on_success"] = editors["notify_on_success"].isChecked()
            services[svc] = merged

            if editors["enabled"].isChecked():
                enabled.append(svc)
            else:
                disabled.append(svc)

        cfg = {
            "enabled_services": enabled,
            "disabled_services": disabled,
            "services": services,
            "ollama_model": self._model_combo.currentText(),
            "notification_mode": (
                "always" if self._notif_always.isChecked() else "failures"
            ),
        }
        APP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        APP_CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
        self._status_label.setText(f"Settings saved to {APP_CONFIG_PATH}")
