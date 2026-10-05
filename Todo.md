# Morning News — Todo

## Current: v0.4.2

### Completed
- [x] Plasmoid widget (initial version)
- [x] PyQt5 desktop app with tray icon
- [x] Dashboard with Sync Services, Latest Activity, New Files, AI Brief
- [x] Collapsible dashboard sections with toggle buttons
- [x] New Files empty state shows message instead of empty table
- [x] Background collection via systemd timer (morning-news-update)
- [x] Ollama AI summary generation with fallback
- [x] SQLite history with click-to-expand detail view
- [x] News extraction from 8 service logs
- [x] Settings persistence to ~/.config/morning-news/config.json
- [x] Notification on failures (desktop tray)
- [x] portfolio-optimizer-sync systemd timer added
- [x] Fix timer column parsing bug (-1 → -2 for UNIT column)
- [x] Launch button (▶ Open) in Sync Services table for services with GUIs
- [x] Help & How-To tab explaining how to add services/apps
- [x] Per-service config: DEFAULT_SERVICE_CONFIGS + load_service_configs() + helpers (get_log_path, get_launch_cmd, get_watch_dir)
- [x] Per-service watch_dir scanning in collector.py (New Files with Service column)
- [x] Settings tab: per-service QGroupBox cards with display name, log path, launch cmd, watch dir, notification prefs
- [x] Dashboard: display_name tooltip, launch cmd from config, 4-column New Files with Service column
- [x] Notifier: per-service notification routing (notify_on_failure/notify_on_success from config)
- [x] T1: Fix stale help text — references LOG_PATHS/SERVICE_LAUNCH_CMDS replaced with DEFAULT_SERVICE_CONFIGS
- [x] T2: Fix QLayoutItem leak in _populate_news() — delete item after takeAt()
- [x] T3: Fix RefreshWorker leak — deleteLater() old worker before replacement
- [x] T4: Cache _get_timer_status() — call once, thread through _get_service_info()
- [x] T5: Add rglob scan limit (5000 files, 30s deadline) to watched directory scanning
- [x] T6: Remove unused imports (Path in summarizer, QStyle in resources)
- [x] T7: Remove dead code (done list in _run_update)
- [x] T8: Add src/__init__.py for package consistency
- [x] T9: Persist dashboard collapse state via SQLite state table
- [x] T10: Add auto-refresh QTimer (10min) in MainWindow
- [x] T11: Add --access-log flag to HTTP --serve mode

### Latest (041)
- [x] P1: Service enable/disable — collector skips disabled, dashboard grays them out (italic/gray)
- [x] P2: Fill missing watch_dir values for manga-updater, ai-wikipedia-sync, fileai-scanner, stokercloud-sync, portfolio-optimizer-sync
- [x] P3: grid-vault-sync news extraction via journalctl (24h range)
- [x] P4: Log-viewer buttons (📄 Log) for CLI-only services via xdg-open; journalctl hint if no log file
- [x] P5: Write implementation-summary.md for 040 spec folder
- [x] P6: Wire notification_mode (all/failures) from config into notifier.py

### Latest (042)
- [x] Fix `QFileDialog` KDE native dialog noise — use `DontUseNativeDialog` in settings browse dialogs
- [x] Fix `UnboundLocalError: disabled` — move assignment before `if disabled:` check
- [x] Fix rsync error code 255 detection — log tail scanning marks services as "failed" when rsync errors detected
- [x] Fix stokercloud sync status — show "warning" when 0 records synced (upstream API issue)
- [x] History tab: Replace QLabel with QTextEdit for scrollable full report view
- [x] History tab: Add "Copy Report Text" button to clipboard-copy report content
- [x] Dashboard: Handle "warning" status with yellow indicator in status bar

### Pending
- [ ] grid-photo-sync, grid-vault-sync, snapshot-sync: GUI apps don't exist — log viewer is the alternative
- [ ] Consider adding generic "view log" option for services with log files in addition to ▶ Open
- [ ] Investigate stokercloud.dk API returning empty data series (all 25 series with 0 data points)
