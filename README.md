# Morning News

PyQt5 desktop dashboard + system tray app that monitors 8 sync services, extracts per-service activity from log files, and generates an AI summary via Ollama.

## Quick Start

```bash
python3 -m app                 # Full GUI
python3 -m app --tray          # Start minimized to tray
python3 -m app --update        # Headless: collect, notify, exit
./launcher.sh                  # Same as python3 -m app
```

## Features

- **Dashboard** — 4 collapsible sections (collapse state persisted): Sync Services status (with ▶ Open buttons for GUI apps and 📄 Log buttons for CLI-only services), Latest Activity news feed, New Files from watched dirs, AI Brief summary
- **Service enable/disable** — Disabled services are excluded from collection and grayed out in table
- **Per-service Settings** — Editable cards for each service: display name, log path, launch command, watch directory, notification preferences (failure/success), enable toggle
- **Help tab** — Explains how to add new services/apps, lists launchable apps, troubleshooting tips
- **System tray** — Green/red icon, double-click to open, Show/Refresh/Quit menu
- **Auto-refresh** — QTimer refreshes dashboard every 10 minutes
- **Background collection** — systemd timer runs `--update` every N minutes, saves report to `~/.cache/morning-news/report.json`
- **News extraction** — All 9 services parsed (including grid-vault-sync via journalctl), e.g., "13 stock tickers updated", "all manga up to date"
- **Settings** — Per-service editable cards (display name, log path, launch command, watch directory, notification prefs) + Ollama model + global notification mode (all/failures). Saves to `~/.config/morning-news/config.json`
- **History** — SQLite-backed report history (`~/.local/share/morning-news/state.db`) with scrollable detail view, Copy Report Text button, per-day JSON archives

## Dashboard Sections

| Section | Source | Shows |
|---------|--------|-------|
| Sync Services | `systemctl --user list-timers` | Timer status, last run, next run, ▶ Open / 📄 Log buttons per service |
| Latest Activity | Log file parsers | Per-service news items (e.g., tickers updated, bytes transferred) |
| New Files | Directory scan (60s max, 5000 file limit) | Recently added files in watched directories |
| AI Brief | Ollama (qwen2.5:3b) | AI-generated summary of all services + news + new files |

## Services Monitored (9)

| Service | Type | News Source |
|---------|------|-------------|
| manga-updater | systemd timer | `sync.log` |
| portfolio-optimizer-sync | systemd timer | `sync_prices.log` |
| grid-photo-sync | systemd timer | `grid_sync_photos.log` |
| stokercloud-sync | systemd timer | `stoker_data.db` |
| snapshot-sync | systemd timer | `snapshots/sync.log` |
| ai-wikipedia-sync | systemd timer | `sync_config.json` |
| fileai-scanner | systemd timer | `.fileai-index.db` |
| grid-vault-sync | systemd timer | journalctl (24h) |
| seagate-sync | qBittorrent hook + cron drain | `~/logs/media-sync.log` + `~/.media-sync-queue/` |

## Project Structure

```
src/
  cli.py          CLI entry point (--update, --json, --serve, --access-log)
  collector.py    Service status collection + news extraction
  summarizer.py   Ollama AI brief generation + fallback
  config.py       DEFAULT_SERVICE_CONFIGS, paths, helper functions
  db.py           SQLite schema + queries (WAL mode) + collapse state helpers
app/
  __main__.py     Entry point (GUI, --tray, --update)
  window.py       MainWindow with QTabWidget, auto-refresh QTimer, tray
  dashboard.py    _CollapsibleSection with persisted state + 4 sections
  help.py         Help & How-To tab (updated for DEFAULT_SERVICE_CONFIGS)
  history.py      Report history from SQLite, scrollable detail view + copy button
  settings.py     Per-service QGroupBox cards with file browse dialogs
  tray.py         QSystemTrayIcon with context menu
  worker.py       RefreshWorker QThread — collect + summarize
  notifier.py     Desktop notifications with per-service routing
  resources.py    SVG icons, stylesheet, APP_VERSION
```

## Config

`~/.config/morning-news/config.json`:

| Key | Default | Purpose |
|-----|---------|---------|
| enabled_services | all | Which services to monitor |
| disabled_services | [] | Disabled services (overrides enabled_services) |
| services | {} | Per-service config dict (display_name, log_path, launch_cmd, watch_dir, notify_on_failure, notify_on_success, enabled) |
| ollama_model | qwen2.5:3b | Ollama model for AI Brief |
| ollama_timeout | 180 | Ollama request timeout |
| notification_mode | failures | all/failures |
| refresh_interval_minutes | 10 | Auto-refresh interval in minutes |

## Makefile

| Target | Purpose |
|--------|---------|
| `install-app` | Set up launcher |
| `install-service` | systemd timer + service for background collection |
| `install-desktop` | KDE autostart entry |
| `install-all` | All of the above |
| `test-app` | Launch app from project dir |

## Architecture

1. **Background** (systemd timer): `cli.py --update` → collect() → summarize() → `report.json` + SQLite
2. **App on start**: reads report.json, populates dashboard
3. **Manual/auto refresh**: QThread calls collect() + summarize(), updates UI + tray
4. **History tab**: reads `morning_reports` table from `~/.local/share/morning-news/state.db`
5. **News extraction**: per-service log parsers extract actionable summaries

## Known Issues

- grid-photo-sync, grid-vault-sync, snapshot-sync are CLI-only (no GUI) — 📄 Log button opens their log file instead
- rsync error code 255 in grid-photo-sync/snapshot-sync means remote host is unreachable (network issue, not a code bug)
- stokercloud.dk API may return empty data series (all 25 series with 0 data points) — shown as "warning" status in dashboard

## CLI Flags

| Flag | Description |
|------|-------------|
| `--update` | Collect data, save report, notify, exit |
| `--json` | Print latest report as JSON |
| `--serve` | Serve report.json via HTTP on 127.0.0.1:8787 |
| `--access-log` | Enable HTTP access log (with --serve) |
| `--tray` | Start GUI minimized to system tray |
| `--verbose` | Enable debug logging (with --update) |
