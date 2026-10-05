from PyQt5.QtGui import QColor, QIcon, QPixmap, QPainter
from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtSvg import QSvgRenderer

APP_NAME = "Morning News"
APP_VERSION = "0.2.0"
CACHE_FILE = None

DARK_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
}
QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background-color: #2d2d2d;
    color: #999;
    padding: 8px 16px;
    border: 1px solid #3c3c3c;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #fff;
    border-bottom-color: #1e1e1e;
}
QTableWidget {
    background-color: #252526;
    color: #d4d4d4;
    gridline-color: #3c3c3c;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}
QTableWidget::item {
    padding: 4px 8px;
}
QTableWidget::item:selected {
    background-color: #094771;
    color: #fff;
}
QHeaderView::section {
    background-color: #2d2d2d;
    color: #ccc;
    padding: 6px;
    border: 1px solid #3c3c3c;
    font-weight: bold;
}
QPushButton {
    background-color: #0e639c;
    color: #fff;
    border: none;
    padding: 6px 16px;
    border-radius: 4px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1177bb;
}
QPushButton:pressed {
    background-color: #094771;
}
QPushButton:disabled {
    background-color: #3c3c3c;
    color: #666;
}
QLabel {
    color: #d4d4d4;
}
QLabel#heading {
    font-size: 18px;
    font-weight: bold;
    color: #fff;
}
QLabel#section {
    font-size: 13px;
    font-weight: bold;
    color: #4fc1ff;
    padding-top: 8px;
}
QLabel#summary {
    font-size: 12px;
    color: #ccc;
    padding: 8px;
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}
QLabel#statusOk {
    color: #4ec9b0;
}
QLabel#statusFail {
    color: #f44747;
}
QLabel#statusUnknown {
    color: #cca700;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QCheckBox {
    color: #d4d4d4;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QComboBox {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #252526;
    color: #d4d4d4;
    selection-background-color: #094771;
}
QGroupBox {
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QTextEdit {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    font-size: 12px;
    padding: 8px;
}
QTextEdit QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 10px;
    border: none;
}
QTextEdit QScrollBar::handle:vertical {
    background-color: #555;
    border-radius: 4px;
    min-height: 20px;
}
QTextEdit QScrollBar::handle:vertical:hover {
    background-color: #777;
}
QTextEdit QScrollBar::add-line:vertical,
QTextEdit QScrollBar::sub-line:vertical {
    height: 0px;
}
QTextEdit QScrollBar::add-page:vertical,
QTextEdit QScrollBar::sub-page:vertical {
    background: none;
}
QStatusBar {
    background-color: #007acc;
    color: #fff;
}
"""


def make_icon(color="#d4d4d4"):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
<circle cx="12" cy="12" r="10" fill="none" stroke="{color}" stroke-width="2"/>
<path d="M12 6v6l4 2" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round"/>
<circle cx="12" cy="12" r="2" fill="{color}"/>
</svg>'''
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def make_status_icon(status):
    if status == "failed":
        color = "#f44747"
        inner = "M12 4L4 20h16z"
    elif status == "completed":
        color = "#4ec9b0"
        inner = "M9 16l-4-4-1.5 1.5L9 19 21 7l-1.5-1.5z"
    else:
        color = "#cca700"
        inner = "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16">
<path d="{inner}" fill="{color}"/>
</svg>'''
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def service_icon_name(status):
    if status == "failed":
        return "❌"
    elif status == "completed":
        return "✅"
    return "⏳"


def ensure_no_qt_conflict():
    import os
    os.environ.setdefault("QT_LOGGING_RULES",
                          "qt.qpa.xcb.xcberror=false;qt.qpa.eglfs.kms=false")
