from PyQt5.QtWidgets import QMainWindow, QTabWidget, QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QCloseEvent
from src.config import AUTO_REFRESH_INTERVAL

from .dashboard import DashboardTab
from .history import HistoryTab
from .settings import SettingsTab
from .help import HelpTab
from .tray import TrayIcon
from .worker import RefreshWorker
from .notifier import Notifier
from .resources import APP_NAME, DARK_STYLESHEET

from src.config import REPORT_PATH
import json


class MainWindow(QMainWindow):
    def __init__(self, start_minimized=False):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(700, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        self._worker = None
        self._data = None

        self._tray = TrayIcon(self)
        self._tray.set_refresh_callback(self.start_refresh)
        self._tray.show()

        self._notifier = Notifier(self._tray)

        tabs = QTabWidget()
        self._dashboard = DashboardTab()
        self._history = HistoryTab()
        self._settings = SettingsTab()
        self._help = HelpTab()
        tabs.addTab(self._dashboard, "Dashboard")
        tabs.addTab(self._history, "History")
        tabs.addTab(self._settings, "Settings")
        tabs.addTab(self._help, "Help")
        self.setCentralWidget(tabs)

        if not start_minimized:
            self.show()
        else:
            QTimer.singleShot(0, self.hide)

        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self.start_refresh)
        self._auto_timer.start(AUTO_REFRESH_INTERVAL * 1000)

        self._load_from_cache()

    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "Morning News",
            "Still running in system tray.",
            self._tray.Information,
            2000,
        )

    def _load_from_cache(self):
        if REPORT_PATH.exists():
            try:
                self._data = json.loads(REPORT_PATH.read_text())
                self._dashboard.set_data(self._data)
                self._update_tray_state()
            except Exception:
                self._dashboard.set_data(None)
        else:
            self._dashboard.set_data(None)

    def start_refresh(self):
        if self._worker:
            if self._worker.isRunning():
                return
            self._worker.deleteLater()
            self._worker = None
        self._auto_timer.stop()
        self._worker = RefreshWorker()
        self._worker.started.connect(lambda: self._dashboard.set_loading(True))
        self._worker.finished.connect(self._on_refresh_done)
        self._worker.error.connect(self._on_refresh_error)
        self._worker.start()

    def _on_refresh_done(self, data, summary):
        self._data = data
        self._dashboard.set_loading(False)
        self._dashboard.set_data(data)
        self._update_tray_state()
        self._history._load_history()
        self._auto_timer.start(AUTO_REFRESH_INTERVAL * 1000)

        failures = data.get("failures", [])
        stats = data.get("summary_stats", {})
        if failures:
            self._notifier.notify_failures(
                failures, stats.get("ok_count", 0), stats.get("total_services", 0)
            )
        else:
            self._notifier.notify_summary(summary)

    def _on_refresh_error(self, msg):
        self._dashboard.set_loading(False)
        self._tray.showMessage(
            "Morning News — Error",
            f"Refresh failed: {msg[:100]}",
            self._tray.Critical,
            5000,
        )
        self._auto_timer.start(AUTO_REFRESH_INTERVAL * 1000)

    def _update_tray_state(self):
        if not self._data:
            return
        failures = self._data.get("failures", [])
        self._tray.set_failure_mode(len(failures) > 0)
