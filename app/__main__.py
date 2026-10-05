#!/usr/bin/env python3
"""Morning News — PyQt5 Desktop App.

Usage:
    python3 -m app                 # Full GUI (window + tray)
    python3 -m app --tray          # Start minimized to tray
    python3 -m app --update        # Run collector, show notification, exit
"""
import sys
import argparse
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication

from .resources import ensure_no_qt_conflict, APP_NAME
from .window import MainWindow
from .worker import RefreshWorker
from .notifier import Notifier
from .tray import TrayIcon


def _run_update():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = TrayIcon()
    tray.show()
    notifier = Notifier(tray)

    worker = RefreshWorker()

    def on_done(data, summary):
        failures = data.get("failures", [])
        stats = data.get("summary_stats", {})
        if failures:
            notifier.notify_failures(
                failures, stats.get("ok_count", 0), stats.get("total_services", 0)
            )
        else:
            notifier.notify_summary(summary)
        QApplication.quit()

    def on_error(msg):
        tray.showMessage("Error", f"Update failed: {msg[:100]}", tray.Critical, 5000)
        QApplication.quit()

    worker.finished.connect(on_done)
    worker.error.connect(on_error)
    worker.start()
    sys.exit(app.exec_())


def main():
    parser = argparse.ArgumentParser(description="Morning News Desktop App")
    parser.add_argument("--tray", action="store_true", help="Start minimized to tray")
    parser.add_argument("--update", action="store_true", help="Run collector, show notification, then exit")
    args = parser.parse_args()

    if args.update:
        _run_update()
        return

    ensure_no_qt_conflict()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(start_minimized=args.tray)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
