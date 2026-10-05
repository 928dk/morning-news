from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QTextEdit,
    QSplitter, QGroupBox, QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from src.db import get_conn
import json


class HistoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_report_text = ""
        self._build_ui()
        self._load_history()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Report History")
        title.setObjectName("heading")
        header.addWidget(title)
        header.addStretch()
        self._refresh_btn = QPushButton("↻ Reload")
        self._refresh_btn.clicked.connect(self._load_history)
        header.addWidget(self._refresh_btn)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Vertical)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Date", "Services OK", "Failed", "New Files", "Summary Preview"]
        )
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self._table.setColumnWidth(0, 110)
        self._table.setColumnWidth(1, 90)
        self._table.setColumnWidth(2, 70)
        self._table.setColumnWidth(3, 80)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._table)

        detail_group = QGroupBox("Full Report")
        detail_layout = QVBoxLayout(detail_group)

        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setObjectName("summary")
        self._detail_text.setPlaceholderText("Select a report to view details")
        detail_layout.addWidget(self._detail_text)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._copy_btn = QPushButton("Copy Report Text")
        self._copy_btn.setFixedWidth(160)
        self._copy_btn.clicked.connect(self._copy_report)
        btn_row.addWidget(self._copy_btn)
        detail_layout.addLayout(btn_row)

        splitter.addWidget(detail_group)
        splitter.setSizes([250, 200])
        layout.addWidget(splitter)

    def _load_history(self):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT report_date, raw_data, llm_summary, created_at "
                "FROM morning_reports ORDER BY id DESC LIMIT 50"
            ).fetchall()
            conn.close()
        except Exception:
            rows = []

        self._table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            date_item = QTableWidgetItem(row["report_date"])
            self._table.setItem(i, 0, date_item)

            try:
                raw = json.loads(row["raw_data"])
                stats = raw.get("summary_stats", {})
            except Exception:
                raw = {}
                stats = {}

            ok_item = QTableWidgetItem(str(stats.get("ok_count", "")))
            ok_item.setTextAlignment(Qt.AlignCenter)
            ok_item.setForeground(QColor("#4ec9b0"))
            self._table.setItem(i, 1, ok_item)

            failed_count = stats.get("failed_count", 0)
            fail_item = QTableWidgetItem(str(failed_count))
            fail_item.setTextAlignment(Qt.AlignCenter)
            if failed_count:
                fail_item.setForeground(QColor("#f44747"))
            self._table.setItem(i, 2, fail_item)

            files_item = QTableWidgetItem(str(stats.get("new_file_count", "")))
            files_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 3, files_item)

            summary_text = row["llm_summary"] or ""
            snippet = summary_text[:80] + ("..." if len(summary_text) > 80 else "")
            self._table.setItem(i, 4, QTableWidgetItem(snippet))

            self._table.item(i, 0).setData(Qt.UserRole, row["report_date"])

        self._table.resizeRowsToContents()

    def _on_selection_changed(self):
        selected = self._table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        date_item = self._table.item(row, 0)
        if not date_item:
            return
        report_date = date_item.data(Qt.UserRole)
        if not report_date:
            return

        try:
            conn = get_conn()
            row = conn.execute(
                "SELECT raw_data, llm_summary FROM morning_reports "
                "WHERE report_date=? ORDER BY id DESC LIMIT 1",
                (report_date,),
            ).fetchone()
            conn.close()
        except Exception:
            row = None

        if not row:
            self._detail_text.setPlainText("No details available.")
            self._current_report_text = ""
            return

        summary = row["llm_summary"] or "No AI brief."
        try:
            raw = json.loads(row["raw_data"])
            services = raw.get("services", [])
            svc_lines = []
            for svc in services:
                svc_lines.append(
                    f"  {svc.get('name')}: {svc.get('status', '?')}"
                    f"  (last: {svc.get('last_run', '—')})"
                )
                details = svc.get("details", "")
                if details:
                    truncated = details[:200] + ("..." if len(details) > 200 else "")
                    svc_lines.append(f"    └ {truncated}")
            news_items = raw.get("news", [])
            news_lines = []
            for item in news_items:
                icon = item.get("icon", "•")
                source = item.get("source", "")
                text = item.get("text", "")
                news_lines.append(f"  {icon} {source}: {text}")
            new_files = raw.get("new_files", [])
            file_lines = [
                f"  {f['directory']}: {f['count']} files ({f.get('total_size', '')})"
                for f in new_files
            ]
        except Exception:
            svc_lines = []
            news_lines = []
            file_lines = []

        parts = [f"Date: {report_date}", "", "AI Brief:", summary]
        if svc_lines:
            parts += ["", "Services:"] + svc_lines
        if news_lines:
            parts += ["", "Latest Activity:"] + news_lines
        if file_lines:
            parts += ["", "New Files:"] + file_lines

        report_text = "\n".join(parts)
        self._current_report_text = report_text
        self._detail_text.setPlainText(report_text)

    def _copy_report(self):
        if self._current_report_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._current_report_text)
