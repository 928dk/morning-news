import subprocess

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame,
    QHeaderView, QSizePolicy, QGridLayout,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor

from pathlib import Path

from .resources import service_icon_name
from src.config import load_service_configs, get_launch_cmd, get_log_path
from src.db import save_collapse_state, load_collapse_state


class _CollapsibleSection(QWidget):
    def __init__(self, title, content_widget, parent=None, state_key=None):
        super().__init__(parent)
        self._title = title
        self._content = content_widget
        self._state_key = state_key
        start_expanded = load_collapse_state(state_key) if state_key else True
        self._expanded = start_expanded

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._btn = QPushButton()
        self._btn.setObjectName("section")
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.setFlat(True)
        self._btn.clicked.connect(self._toggle)
        self._update_text()
        layout.addWidget(self._btn)

        layout.addWidget(content_widget)

        content_widget.setVisible(start_expanded)

    def _toggle(self):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._update_text()
        if self._state_key:
            save_collapse_state(self._state_key, self._expanded)

    def _update_text(self):
        arrow = "▼" if self._expanded else "▶"
        self._btn.setText(f"{arrow} {self._title}")


class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        title = QLabel("☕ Morning News")
        title.setObjectName("heading")
        header_row.addWidget(title)
        header_row.addStretch()
        self._ts_label = QLabel("")
        self._ts_label.setStyleSheet("color: #888; font-size: 11px;")
        header_row.addWidget(self._ts_label)
        self._refresh_btn = QPushButton("↻ Refresh")
        self._refresh_btn.setFixedWidth(100)
        self._refresh_btn.clicked.connect(self._on_refresh)
        header_row.addWidget(self._refresh_btn)
        layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(8)

        self._svc_table = QTableWidget()
        self._svc_table.setColumnCount(5)
        self._svc_table.setHorizontalHeaderLabels(["", "Service", "Last Run", "Status", "Launch"])
        self._svc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._svc_table.setColumnWidth(0, 28)
        self._svc_table.setColumnWidth(2, 180)
        self._svc_table.setColumnWidth(3, 100)
        self._svc_table.setColumnWidth(4, 110)
        self._svc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._svc_table.setSelectionMode(QTableWidget.NoSelection)
        self._svc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._svc_table.setShowGrid(False)
        self._svc_table.setMaximumHeight(300)
        self._svc_table.verticalHeader().setVisible(False)
        svc_section = _CollapsibleSection("Sync Services", self._svc_table, state_key="svc")
        inner_layout.addWidget(svc_section)

        self._news_widget = QWidget()
        self._news_layout = QVBoxLayout(self._news_widget)
        self._news_layout.setContentsMargins(0, 0, 0, 0)
        self._news_layout.setSpacing(2)
        self._news_placeholder = QLabel("No activity data yet.")
        self._news_placeholder.setStyleSheet("color: #888; font-size: 11px; padding: 4px 8px;")
        self._news_layout.addWidget(self._news_placeholder)
        news_section = _CollapsibleSection("Latest Activity", self._news_widget, state_key="news")
        inner_layout.addWidget(news_section)

        self._files_table = QTableWidget()
        self._files_table.setColumnCount(4)
        self._files_table.setHorizontalHeaderLabels(["Service", "Directory", "Count", "Size"])
        self._files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._files_table.setColumnWidth(0, 150)
        self._files_table.setColumnWidth(2, 80)
        self._files_table.setColumnWidth(3, 100)
        self._files_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._files_table.setSelectionMode(QTableWidget.NoSelection)
        self._files_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._files_table.setShowGrid(False)
        self._files_table.setMaximumHeight(200)
        self._files_table.verticalHeader().setVisible(False)
        self._files_empty_label = QLabel("No new files detected.")
        self._files_empty_label.setStyleSheet("color: #888; font-size: 11px; padding: 4px 8px;")
        self._files_empty_label.setVisible(False)
        inner_layout.addWidget(self._files_empty_label)
        files_section = _CollapsibleSection("New Files", self._files_table, state_key="files")
        inner_layout.addWidget(files_section)

        self._summary_label = QLabel("")
        self._summary_label.setObjectName("summary")
        self._summary_label.setWordWrap(True)
        brief_section = _CollapsibleSection("AI Brief", self._summary_label, state_key="brief")
        inner_layout.addWidget(brief_section)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        self._status_bar = QLabel("")
        self._status_bar.setFixedHeight(20)
        self._status_bar.setStyleSheet(
            "background-color: #007acc; color: #fff; padding: 2px 8px; font-size: 11px;"
        )
        layout.addWidget(self._status_bar)

    def _on_refresh(self):
        w = self.window()
        if w and hasattr(w, 'start_refresh'):
            w.start_refresh()

    def _launch_service(self, name):
        cmd = get_launch_cmd(name)
        if not cmd:
            return
        try:
            subprocess.Popen(cmd, start_new_session=True)
        except Exception as e:
            self._status_bar.setText(f"Launch failed: {e}")

    def _view_log(self, name):
        log_path_str = get_log_path(name)
        if not log_path_str:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Log File",
                f"No log file configured for {name}.\nCheck journalctl: "
                f"journalctl --user -u {name}.service")
            return
        log_path = Path(log_path_str)
        if not log_path.exists():
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Log File Not Found",
                f"Log file not found:\n{log_path}\n\nCheck journalctl: "
                f"journalctl --user -u {name}.service")
            return
        try:
            subprocess.Popen(["xdg-open", str(log_path)], start_new_session=True)
        except Exception as e:
            self._status_bar.setText(f"Open log failed: {e}")

    def _populate_news(self, news_items):
        while self._news_layout.count():
            item = self._news_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            del item
        if not news_items:
            placeholder = QLabel("No activity data yet.")
            placeholder.setStyleSheet("color: #888; font-size: 11px; padding: 4px 8px;")
            self._news_layout.addWidget(placeholder)
            return
        for item in news_items:
            icon = item.get("icon", "•")
            source = item.get("source", "")
            text = item.get("text", "")
            label = QLabel(f"{icon} <b>{source}:</b> {text}")
            label.setWordWrap(True)
            label.setStyleSheet("color: #ccc; font-size: 11px; padding: 2px 8px;")
            self._news_layout.addWidget(label)

    def set_data(self, data):
        self._data = data
        if not data:
            self._svc_table.setRowCount(0)
            self._files_table.setRowCount(0)
            self._summary_label.setText("No report yet.")
            self._ts_label.setText("")
            self._status_bar.setText("No data")
            return

        services = data.get("services", [])
        self._svc_table.setRowCount(len(services))
        svc_configs = load_service_configs()
        for i, svc in enumerate(services):
            icon_item = QTableWidgetItem(service_icon_name(svc.get("status")))
            icon_item.setTextAlignment(Qt.AlignCenter)
            self._svc_table.setItem(i, 0, icon_item)
            name = svc.get("name", "")
            cfg = svc_configs.get(name, {})
            disabled = not cfg.get("enabled", True)
            display_name = cfg.get("display_name", name)
            name_item = QTableWidgetItem(display_name)
            name_item.setToolTip(name)
            if disabled:
                font = name_item.font()
                font.setItalic(True)
                name_item.setFont(font)
                name_item.setForeground(QColor("#888"))
            self._svc_table.setItem(i, 1, name_item)
            self._svc_table.setItem(i, 2, QTableWidgetItem(svc.get("last_run", "—")))
            status = svc.get("status", "unknown")
            status_item = QTableWidgetItem(status)
            if status == "failed":
                status_item.setForeground(QColor("#f44747"))
            elif status == "completed":
                status_item.setForeground(QColor("#4ec9b0"))
            elif status == "warning":
                status_item.setForeground(QColor("#cca700"))
            else:
                status_item.setForeground(QColor("#cca700"))
            self._svc_table.setItem(i, 3, status_item)
            launch_cmd = cfg.get("launch_cmd", "")
            log_path_str = cfg.get("log_path", "")
            if launch_cmd:
                btn = QPushButton("▶ Open")
                btn.setFixedWidth(80)
                btn.setEnabled(not disabled)
                btn.clicked.connect(lambda checked, n=name: self._launch_service(n))
                self._svc_table.setCellWidget(i, 4, btn)
            elif log_path_str:
                btn = QPushButton("📄 Log")
                btn.setFixedWidth(80)
                btn.setToolTip(f"Open log: {log_path_str}")
                btn.clicked.connect(lambda checked, n=name: self._view_log(n))
                self._svc_table.setCellWidget(i, 4, btn)
            else:
                self._svc_table.setItem(i, 4, QTableWidgetItem("—"))
        self._svc_table.resizeRowsToContents()

        self._populate_news(data.get("news", []))

        new_files = data.get("new_files", [])
        has_files = len(new_files) > 0
        self._files_table.setVisible(has_files)
        self._files_empty_label.setVisible(not has_files)
        self._files_table.setRowCount(len(new_files))
        for i, f in enumerate(new_files):
            svc_name = f.get("service", "")
            cfg = svc_configs.get(svc_name, {})
            display = cfg.get("display_name", svc_name)
            self._files_table.setItem(i, 0, QTableWidgetItem(display))
            self._files_table.setItem(i, 1, QTableWidgetItem(f.get("directory", "")))
            self._files_table.setItem(i, 2, QTableWidgetItem(str(f.get("count", ""))))
            self._files_table.setItem(i, 3, QTableWidgetItem(f.get("total_size", "")))
        self._files_table.resizeRowsToContents()

        summary = data.get("summary", "")
        self._summary_label.setText(summary or "All clear — no issues.")

        gen_at = data.get("generated_at", "")
        self._ts_label.setText(gen_at[:19] if gen_at else "")

        stats = data.get("summary_stats", {})
        ok = stats.get("ok_count", 0)
        total = stats.get("total_services", 0)
        failed = stats.get("failed_count", 0)
        warnings = stats.get("warning_count", 0)
        if failed or warnings:
            parts = []
            if failed:
                parts.append(f"⚠ {failed} failed")
            if warnings:
                parts.append(f"⚠ {warnings} warning")
            self._status_bar.setText(
                " | ".join(parts) +
                f"  |  {ok}/{total} OK"
                f"  |  {stats.get('new_file_count', 0)} new files"
            )
        else:
            self._status_bar.setText(
                f"✓ {ok}/{total} OK"
                f"  |  {stats.get('new_file_count', 0)} new files"
            )

    def set_loading(self, loading):
        self._refresh_btn.setEnabled(not loading)
        if loading:
            self._status_bar.setText("Refreshing...")
