PLASMOID_DIR := $(HOME)/.local/share/plasma/plasmoids/morning-news
SYSTEMD_USER_DIR := $(HOME)/.config/systemd/user
AUTOSTART_DIR := $(HOME)/.config/autostart
PROJECT_ROOT := $(HOME)/projects/Client/morning-news
SRC := src/cli.py

.PHONY: install uninstall test install-service uninstall-service \
        install-all uninstall-all reinstall \
        install-app uninstall-app test-app \
        install-desktop uninstall-desktop

install:
	@echo "Installing plasmoid to $(PLASMOID_DIR)..."
	@mkdir -p $(PLASMOID_DIR)
	@cp -r package/* $(PLASMOID_DIR)/
	@echo "Done. Restart Plasma: systemctl --user restart plasma-plasmoids (or logout/login)"

uninstall:
	@echo "Removing plasmoid from $(PLASMOID_DIR)..."
	@rm -rf $(PLASMOID_DIR)
	@echo "Uninstalled."

reinstall: uninstall install

test:
	@echo "Launching plasmoid in windowed mode..."
	@plasmawindowed org.kde.plasma.morning-news

install-service:
	@echo "Installing systemd user service + timer..."
	@mkdir -p $(SYSTEMD_USER_DIR)
	@cp systemd/morning-news-update.service $(SYSTEMD_USER_DIR)/
	@cp systemd/morning-news-update.timer $(SYSTEMD_USER_DIR)/
	@cp systemd/portfolio-optimizer-sync.service $(SYSTEMD_USER_DIR)/
	@cp systemd/portfolio-optimizer-sync.timer $(SYSTEMD_USER_DIR)/
	@systemctl --user daemon-reload
	@systemctl --user enable --now morning-news-update.timer
	@systemctl --user enable --now portfolio-optimizer-sync.timer
	@echo "Service enabled. Status:"
	@systemctl --user status morning-news-update.timer --no-pager | head -8
	@echo ""
	@systemctl --user status portfolio-optimizer-sync.timer --no-pager | head -5

uninstall-service:
	@echo "Stopping and removing systemd user service + timer..."
	-systemctl --user stop morning-news-update.timer 2>/dev/null
	-systemctl --user disable morning-news-update.timer 2>/dev/null
	@rm -f $(SYSTEMD_USER_DIR)/morning-news-update.service
	@rm -f $(SYSTEMD_USER_DIR)/morning-news-update.timer
	@systemctl --user daemon-reload
	@echo "Service uninstalled."

install-app:
	@echo "Installing PyQt5 app..."
	@chmod +x launcher.sh
	@echo "App installed at $(PROJECT_ROOT)"
	@echo "Run: python3 -m app  or  ./launcher.sh"
	@echo ""

uninstall-app:
	@echo "PyQt5 app has no installed files outside project tree."
	@echo "Remove project directory to uninstall."

install-desktop:
	@echo "Installing KDE autostart .desktop..."
	@mkdir -p $(AUTOSTART_DIR)
	@cp org.morningnews.app.desktop $(AUTOSTART_DIR)/morning-news.desktop
	@chmod +x $(AUTOSTART_DIR)/morning-news.desktop
	@echo "Installed to $(AUTOSTART_DIR)/morning-news.desktop"

uninstall-desktop:
	@echo "Removing KDE autostart .desktop..."
	@rm -f $(AUTOSTART_DIR)/morning-news.desktop
	@echo "Uninstalled."

test-app:
	@echo "Launching Morning News app..."
	@python3 -m app

install-all: install install-service install-desktop
uninstall-all: uninstall-service uninstall uninstall-desktop
