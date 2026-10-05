from PyQt5.QtWidgets import QSystemTrayIcon

from src.config import load_service_configs, APP_CONFIG_PATH
import json


class Notifier:
    def __init__(self, tray_icon):
        self.tray = tray_icon
        self._mode = self._load_mode()

    def _load_mode(self):
        try:
            if APP_CONFIG_PATH.exists():
                cfg = json.loads(APP_CONFIG_PATH.read_text())
                return cfg.get("notification_mode", "failures")
        except Exception:
            pass
        return "failures"

    def notify_failures(self, failures, ok_count, total):
        if not failures:
            return
        cfg = load_service_configs()
        notified = []
        for name in failures:
            entry = cfg.get(name, {})
            if entry.get("notify_on_failure", True):
                notified.append(name)
        if not notified:
            return
        msg = f"{len(notified)} service(s) failed: {', '.join(notified[:3])}"
        if len(notified) > 3:
            msg += f" (+{len(notified)-3} more)"
        self.tray.showMessage(
            "Morning News — Failures Detected",
            msg,
            QSystemTrayIcon.Warning,
            5000,
        )

    def notify_summary(self, text):
        if self._mode not in ("all", "always"):
            return
        self.tray.showMessage(
            "Morning News — Updated",
            text[:120],
            QSystemTrayIcon.Information,
            3000,
        )
