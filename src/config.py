from pathlib import Path
import json

CACHE_DIR = Path.home() / ".cache" / "morning-news"
DATA_DIR = Path.home() / ".local" / "share" / "morning-news"
DB_PATH = DATA_DIR / "state.db"
ARCHIVE_DIR = DATA_DIR
REPORT_PATH = CACHE_DIR / "report.json"
APP_CONFIG_PATH = Path.home() / ".config" / "morning-news" / "config.json"

SYNC_SERVICES = [
    "manga-updater",
    "ai-wikipedia-sync",
    "fileai-scanner",
    "grid-photo-sync",
    "grid-vault-sync",
    "stokercloud-sync",
    "snapshot-sync",
    "portfolio-optimizer-sync",
    "seagate-sync",
]

ALWAYS_ON_SERVICES = [
    "vaultmind",
    "nexus-worker",
    "mediabox",
    "transfer-server",
    "portfolio-optimizer",
    "litellm",
    "openviking",
]

STOKERCLOUD_DB = Path.home() / "projects/Custom-Firmware/NBE-v7-wood-pellet-stoker/stoker_data.db"
FILEAI_INDEX_DB = Path.home() / ".fileai-index.db"
VAULT_GIT_DIR = Path.home() / "Sync/vault-git"

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"
AUTO_REFRESH_INTERVAL = 600

DEFAULT_SERVICE_CONFIGS = {
    "manga-updater": {
        "display_name": "Manga Updater",
        "timer_name": "datasync-manga-updater",
        "service_name": "datasync-manga-updater",
        "log_path": str(Path.home() / ".synced/manga-updater.log"),
        "launch_cmd": str(Path.home() / "projects/Client/manga-updater/launch.sh"),
        "watch_dir": str(Path.home() / "Manga_News_Downloads"),
        "sync_config_path": "",
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
    "ai-wikipedia-sync": {
        "display_name": "AI Wikipedia Sync",
        "log_path": "",
        "launch_cmd": f"python3 {Path.home()}/projects/Client/ai-wikipedia/scraper_package/gui.py",
        "watch_dir": str(Path.home() / "projects/Client/ai-wikipedia-sync/docs"),
        "sync_config_path": str(Path.home() / ".local/share/com.ai-wikipedia.app/wikipedia/sync_config.json"),
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
    "fileai-scanner": {
        "display_name": "FileAI Scanner",
        "log_path": "",
        "launch_cmd": f"python3 {Path.home()}/projects/Client/file-ai/gui.py",
        "watch_dir": str(Path.home() / "bigfiles_setup"),
        "sync_config_path": "",
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
    "grid-photo-sync": {
        "display_name": "Grid Photo Sync",
        "log_path": str(Path.home() / "grid_sync_photos.log"),
        "launch_cmd": "",
        "watch_dir": str(Path.home() / "Photos"),
        "sync_config_path": "",
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
    "grid-vault-sync": {
        "display_name": "Grid Vault Sync",
        "log_path": "",
        "launch_cmd": "",
        "watch_dir": str(Path.home() / "Sync/vault-git"),
        "sync_config_path": "",
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
    "stokercloud-sync": {
        "display_name": "StokerCloud Sync",
        "log_path": str(Path.home() / "projects/Custom-Firmware/NBE-v7-wood-pellet-stoker/sync.log"),
        "launch_cmd": f"python3 {Path.home()}/projects/Custom-Firmware/NBE-v7-wood-pellet-stoker/stoker_gui.py",
        "watch_dir": str(Path.home() / "StokerCloud"),
        "sync_config_path": "",
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
    "snapshot-sync": {
        "display_name": "Snapshot Sync",
        "log_path": str(Path.home() / "snapshots/sync.log"),
        "launch_cmd": "",
        "watch_dir": str(Path.home() / "snapshots"),
        "sync_config_path": "",
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
    "portfolio-optimizer-sync": {
        "display_name": "Portfolio Optimizer Sync",
        "timer_name": "datasync-portfolio-optimizer",
        "service_name": "datasync-portfolio-optimizer",
        "log_path": str(Path.home() / "projects/Client/portfolio-optimizer-pro/logs/sync_prices.log"),
        "launch_cmd": f"python3 {Path.home()}/projects/Client/portfolio-optimizer-pro/src/main.py",
        "watch_dir": str(Path.home() / "projects/Client/portfolio-optimizer-pro/reports"),
        "sync_config_path": "",
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
    "seagate-sync": {
        "display_name": "Seagate Sync",
        "timer_name": "datasync-seagate-media",
        "service_name": "datasync-seagate-media",
        "log_path": str(Path.home() / "logs/media-sync.log"),
        "launch_cmd": "",
        "watch_dir": str(Path.home() / ".media-sync-queue"),
        "sync_config_path": "",
        "notify_on_failure": True,
        "notify_on_success": False,
        "enabled": True,
    },
}


def _load_json():
    if not APP_CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(APP_CONFIG_PATH.read_text())
    except Exception:
        return {}


def _write_json(cfg):
    APP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    APP_CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def load_service_configs():
    cfg = _load_json()
    overrides = cfg.get("services", {})
    result = {}
    for name in SYNC_SERVICES:
        entry = dict(DEFAULT_SERVICE_CONFIGS.get(name, {}))
        if name in overrides:
            entry.update(overrides[name])
        result[name] = entry
    return result


def get_log_path(name, configs=None):
    if configs is None:
        configs = load_service_configs()
    entry = configs.get(name, {})
    return entry.get("log_path", "")


def get_launch_cmd(name, configs=None):
    if configs is None:
        configs = load_service_configs()
    entry = configs.get(name, {})
    raw = entry.get("launch_cmd", "")
    if not raw:
        return []
    return raw.split(maxsplit=1)


def get_watch_dir(name, configs=None):
    if configs is None:
        configs = load_service_configs()
    entry = configs.get(name, {})
    return entry.get("watch_dir", "")


def get_sync_config_path(name, configs=None):
    if configs is None:
        configs = load_service_configs()
    entry = configs.get(name, {})
    return entry.get("sync_config_path", "")
