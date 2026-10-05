# Morning News — Specification

## Purpose
Dashboard + system tray app that monitors 8 sync services, extracts per-service activity from log files, generates an AI summary via Ollama, and shows new files from watched directories.

## Architecture

### Components

```
src/cli.py            CLI entry: --update (collect+summarize), --json, --serve, --access-log
src/collector.py      Collect service timers → OS timers, news extraction from logs
src/summarizer.py     Build prompt from services + news + new files → Ollama → fallback
src/config.py         DEFAULT_SERVICE_CONFIGS, load_service_configs(), helper functions
src/db.py             SQLite schema (sync_log, morning_reports, state), WAL mode, collapse state helpers

app/__main__.py       Entry: python3 -m app (GUI), --tray (minimized), --update (headless)
app/window.py         MainWindow: QTabWidget (Dashboard, History, Settings, Help), auto-refresh QTimer (10min), tray
app/dashboard.py      4 collapsible sections with persisted state + content widgets; ▶ Open buttons + Service column
app/settings.py       Per-service QGroupBox cards with display name, log path, launch cmd, watch dir, notification prefs
app/help.py           Help & How-To tab explaining service setup and launchable apps
app/history.py        Report history from SQLite, click-to-expand
app/notifier.py       Desktop notifications with per-service routing
app/tray.py           QSystemTrayIcon, context menu, double-click
app/worker.py         RefreshWorker QThread — non-blocking collect + summarize
app/resources.py      SVG icons, DARK_STYLESHEET, APP_VERSION
```

### Data Flow

1. systemd timer → `cli.py --update` → collect() → summarize() → report.json + SQLite
2. App start → reads report.json → populates dashboard
3. Manual/auto refresh (10min) → QThread → collect() + summarize() → UI + tray update
4. History tab → SQLite morning_reports table

### News Extraction

| Service | Source Log | Key Outputs |
|---------|------------|-------------|
| manga-updater | `~/Client/manga-updater/sync.log` | "X titles synced", "all manga up to date" |
| ai-wikipedia-sync | `~/Client/ai-wikipedia-sync/sync.log` | "X topics completed", "X errors" |
| fileai-scanner | `~/Client/fileai-scanner/sync.log` | "X new/new_changed files", "unchanged" |
| grid-photo-sync | `~/Client/grid-photo-sync/sync.log` | "X items synced", "No new files" |
| grid-vault-sync | journalctl (24h) | "X journal entries — last line" |
| stokercloud-sync | `~/Client/stokercloud-sync/sync.log` | "X invoices/contacts/offers", "nothing new" |
| snapshot-sync | `~/Client/snapshot-sync/sync.log` | "X snapshots cleaned", "none dropped" |
| portfolio-optimizer-sync | `~/Client/portfolio-optimizer-sync/sync.log` | "X tickers updated", "still initializing" |

### Launch / Log Buttons

| Service | Button | Action |
|---------|--------|--------|
| fileai-scanner | ▶ Open | Launches GUI |
| manga-updater | ▶ Open | Launches browser |
| stokercloud-sync | ▶ Open | Launches GUI |
| portfolio-optimizer-sync | ▶ Open | Launches GUI |
| grid-photo-sync | 📄 Log | Opens log file via xdg-open (CLI-only) |
| snapshot-sync | 📄 Log | Opens log file via xdg-open (CLI-only) |
| grid-vault-sync | 📄 Log | Shows journalctl hint (no log file) |

### Per-service Watched Directories

| Service | Watched Directory |
|---------|-------------------|
| ai-wikipedia-sync | `~/Client/ai-wikipedia-sync/docs` |
| fileai-scanner | `~/bigfiles_setup` |
| grid-photo-sync | `~/FLEET_HOST_Photos` (5000 file / 30s limit) |
| grid-vault-sync | `~/GDrive_Vault` |
| manga-updater | `~/Manga_News_Downloads` |
| snapshot-sync | `~/snapshots` |
| stokercloud-sync | `~/StokerCloud` |
| portfolio-optimizer-sync | `~/Client/portfolio-optimizer-sync/reports` |

## Configuration

### Global Config File

`~/.config/morning-news/config.json`:

```json
{
  "enabled_services": ["manga-updater", "ai-wikipedia-sync", ...],
  "disabled_services": [],
  "ollama_model": "qwen2.5:3b",
  "ollama_timeout": 180,
  "notify_mode": "all",
  "refresh_interval_minutes": 10,
  "services": {
    "manga-updater": {
      "display_name": "Manga Updater",
      "log_path": "$HOME/projects/Client/manga-updater/sync.log",
      "launch_cmd": "$HOME/projects/Client/manga-updater/launch.sh",
      "watch_dir": "$HOME/Manga_News_Downloads",
      "notify_on_failure": true,
      "notify_on_success": false,
      "enabled": true
    }
  }
}
```

- All per-service fields optional; missing fields fall back to `src/config.py` DEFAULT_SERVICE_CONFIGS.
- Settings tab provides editable QGroupBox cards with file browse dialogs.

### Adding a New Service

1. Add entry to `DEFAULT_SERVICE_CONFIGS` dict in `src/config.py`
2. Add log parser in `_get_service_news()` function in `src/collector.py`
3. Add entry to `SYNC_SERVICES` list in `src/config.py`
4. Restart morning-news — new service appears in Settings tab and Dashboard

### Settings Tab UI

Each service has its own QGroupBox with:
- **Display name** — QLineEdit
- **Enabled** — QCheckBox
- **Log path** — QLineEdit + Browse button (QFileDialog.getOpenFileName, DontUseNativeDialog)
- **Launch command** — QLineEdit + Browse button (QFileDialog.getOpenFileName, DontUseNativeDialog)
- **Watch directory** — QLineEdit + Browse button (QFileDialog.getExistingDirectory, DontUseNativeDialog)
- **Notify on failure** — QCheckBox (default: checked)
- **Notify on success** — QCheckBox (default: unchecked)
- **Save** button saves to config.json with `services` dict

## Per-Service Config Model

```python
DEFAULT_SERVICE_CONFIGS = {
    "service-name": {
        "display_name": str,
        "log_path": str,
        "launch_cmd": str,
        "watch_dir": str,
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    }
}
```

## Key Implementation Details

- Timer status cached: `_get_timer_status()` called once in `collect()`, threaded through `_get_service_info()`
- Directory scans bounded: `_MAX_SCAN_FILES = 5000`, `_SCAN_DEADLINE_SEC = 30`
- Worker lifecycle: old `RefreshWorker` `deleteLater()`'d before replacement
- Layout cleanup: `QLayoutItem` explicitly deleted in `_populate_news()`
- Collapse state: persisted in SQLite `state` table, restored on app start
- Auto-refresh: QTimer fires every `AUTO_REFRESH_INTERVAL` (600s), paused during active refresh
- Enable/disable: collector skips services with `enabled: False`; dashboard grays them out (italic, #888)
- Notification mode: notifier.py reads `notification_mode` from config; summary only fires when mode is "all" or "always"
- Log viewer: CLI-only services get 📄 Log button; opens via `xdg-open` or shows journalctl hint if no log file
- Disabled service name rendered in italic with gray foreground in the dashboard table

## Persistent State

- `~/.local/share/morning-news/state.db` — SQLite database (WAL mode)
- Tables: `sync_log`, `morning_reports`, `state` (includes collapse_* keys)
- Daily JSON archive: `report-YYYY-MM-DD.json` in same directory

## Cached / Runtime Data

- `~/.cache/morning-news/report.json` — last full report (services + news + new files + AI brief)
- `~/.cache/morning-news/morning-news.log` — app log

## Tray Icon

- Green: last collection successful
- Red: last collection had failures
- Context menu: Show, Refresh, Quit
- Double-click: toggle window visibility

## Notifications

- Per-service routing: reads `notify_on_failure`/`notify_on_success` from merged config
- Failure notification: "X service(s) failed: ..." with up to 3 names + overflow count
- Success summary: first 120 chars of AI brief
- Uses `QSystemTrayIcon.showMessage()`

## CLI Flags

| Flag | Description |
|------|-------------|
| `--update` | Collect data, save report, notify, exit |
| `--json` | Print latest report as JSON |
| `--serve` | Serve report.json via HTTP (127.0.0.1:8787) |
| `--access-log` | Enable HTTP access log (with --serve) |
| `--tray` | Start GUI minimized to system tray |

## Tests

```
cd $HOME/projects/Client/morning-news
PYTHONPATH=. python3 -m pytest test/ -v
```

## License

MIT — see LICENSE file.
