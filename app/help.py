from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from PyQt5.QtCore import Qt


class HelpTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Help & How-To")
        title.setObjectName("heading")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(16)
        inner_layout.setContentsMargins(0, 0, 0, 0)

        inner_layout.addWidget(self._section(
            "About Morning News",
            "Morning News is a dashboard that monitors your sync services, "
            "displays recent activity, tracks new files, and summarizes "
            "everything with an AI-generated brief."
        ))

        inner_layout.addWidget(self._section(
            "The Dashboard",
            "<b>Sync Services</b> — shows all monitored systemd timer services, "
            "their last run time, status (completed/failed/unknown), and a "
            "<b>▶ Open</b> button to launch the associated GUI app where one exists.<br><br>"
            "<b>Latest Activity</b> — recent events from each service.<br><br>"
            "<b>New Files</b> — files detected in watched directories.<br><br>"
            "<b>AI Brief</b> — an AI-generated summary of the current state."
        ))

        inner_layout.addWidget(self._section(
            "How to Add a New Service/App",
            "To add a new service to the dashboard, follow these steps:"
            "<ol>"
            "<li><b>Create a systemd timer</b> for your service. "
            "Example: <code>~/.config/systemd/user/my-service.service</code> "
            "and <code>my-service.timer</code>. "
            "(Skip if your service is not timer-driven, e.g. a qBittorrent hook "
            "like <b>seagate-sync</b> — status is then derived from the log.)</li>"
            "<li><b>Add the service name</b> to the <code>SYNC_SERVICES</code> "
            "list and an entry to <code>DEFAULT_SERVICE_CONFIGS</code> "
            "in <code>src/config.py</code>.</li>"
            "<li><b>Add a log parser</b> in <code>_get_service_news()</code> in "
            "<code>src/collector.py</code> to extract meaningful activity from the log.</li>"
            "<li><b>Set per-service config fields</b> in <code>DEFAULT_SERVICE_CONFIGS</code>: "
            "<code>display_name</code>, <code>log_path</code>, <code>launch_cmd</code> "
            "(if GUI app), <code>watch_dir</code>, and notification preferences.</li>"
            "<li><b>Restart Morning News</b> — the new service appears "
            "in the Sync Services table on next refresh or app restart.</li>"
            "</ol>"
        ))

        inner_layout.addWidget(self._section(
            "Available Launchable Apps",
            "The following services have a GUI launch button (▶ Open):"
            "<ul>"
            "<li><b>Manga Updater</b> — <code>launch.sh</code></li>"
            "<li><b>AI Wikipedia Sync</b> — <code>python scraper_package/gui.py</code></li>"
            "<li><b>FileAI Scanner</b> — <code>python gui.py</code></li>"
            "<li><b>StokerCloud Sync</b> — <code>python stoker_gui.py</code></li>"
            "<li><b>Portfolio Optimizer Sync</b> — <code>python src/main.py</code></li>"
            "</ul>"
            "<p>To add a new launchable app, set <code>launch_cmd</code> in "
            "<code>DEFAULT_SERVICE_CONFIGS</code> in <code>src/config.py</code>.</p>"
        ))

        inner_layout.addWidget(self._section(
            "Troubleshooting",
            "<b>Service shows \"failed\"</b> — check the systemd journal: "
            "<code>journalctl --user -u &lt;service&gt;.service -n 50</code><br><br>"
            "<b>Launch button missing</b> — the service has no GUI configured. "
            "Set <code>launch_cmd</code> in <code>DEFAULT_SERVICE_CONFIGS</code> in "
            "<code>src/config.py</code> if one exists.<br><br>"
            "<b>No data after restart</b> — "
            "click the <b>↻ Refresh</b> button or wait for the next "
            "automatic update cycle."
        ))

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _section(self, heading, body):
        frame = QFrame()
        frame.setObjectName("helpSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 8)
        heading_label = QLabel(heading)
        heading_label.setObjectName("section")
        layout.addWidget(heading_label)
        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setStyleSheet("color: #ccc; font-size: 12px; padding: 4px 0;")
        layout.addWidget(body_label)
        return frame
