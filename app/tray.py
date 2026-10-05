from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtCore import QTimer

from .resources import make_icon


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(make_icon("#4ec9b0"))
        self.setToolTip("Morning News")

        menu = QMenu()
        self._show_action = QAction("Show Window", self)
        self._show_action.triggered.connect(self._on_show)
        menu.addAction(self._show_action)

        self._refresh_action = QAction("Refresh Now", self)
        self._refresh_action.triggered.connect(self._on_refresh)
        menu.addAction(self._refresh_action)

        menu.addSeparator()

        self._quit_action = QAction("Quit", self)
        self._quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(self._quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

        self._refresh_requested = None

    def set_refresh_callback(self, cb):
        self._refresh_requested = cb

    def _on_show(self):
        w = self.parent()
        if w:
            w.show()
            w.raise_()
            w.activateWindow()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._on_show()

    def _on_refresh(self):
        if self._refresh_requested:
            self._refresh_requested()

    def set_failure_mode(self, has_failures):
        if has_failures:
            self.setIcon(make_icon("#f44747"))
            self.setToolTip("Morning News — Failures detected")
        else:
            self.setIcon(make_icon("#4ec9b0"))
            self.setToolTip("Morning News — All OK")
