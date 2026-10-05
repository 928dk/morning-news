import subprocess
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from .config import (
    SYNC_SERVICES, STOKERCLOUD_DB, VAULT_GIT_DIR,
    load_service_configs, get_log_path, get_sync_config_path, get_watch_dir,
)
from .db import get_last_seen, set_last_seen

_SEAGATE_QUEUE_DIR = Path.home() / ".media-sync-queue"


_DAY_RE = re.compile(r'^[A-Z][a-z]{2}$')
_MAX_SCAN_FILES = 5000
_SCAN_DEADLINE_SEC = 30


def collect() -> dict:
    now = datetime.now().isoformat()
    today = datetime.now().strftime("%Y-%m-%d")

    data = {
        "generated_at": now,
        "date": today,
        "services": [],
        "new_files": [],
        "failures": [],
        "timers": {},
        "summary_stats": {},
    }

    cfg = load_service_configs()

    timers = _get_timer_status()
    data["timers"] = timers
    data["failures"] = _get_failed_services()

    for svc in SYNC_SERVICES:
        if not cfg.get(svc, {}).get("enabled", True):
            continue
        info = _get_service_info(svc, cfg, timers)
        data["services"].append(info)
        if info.get("status") == "failed":
            if svc not in data["failures"]:
                data["failures"].append(svc)

    data["new_files"] = _get_new_files(cfg)
    data["summary_stats"] = _compute_stats(data)
    data["news"] = _extract_news(data, cfg)

    return data


def _run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError:
        return "", "not found", -1
    except subprocess.TimeoutExpired:
        return "", "timeout", -1


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")
_TZ_RE = re.compile(r"^[A-Za-z]+$")


def _get_timer_status():
    out, _, _ = _run(["systemctl", "--user", "list-timers", "--all"])
    timers = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 6 or not parts[-2].endswith(".timer"):
            continue
        unit = parts[-2]
        body = parts[:-2]
        next_run = None
        last_run = None
        passed = None
        starts = [
            i
            for i in range(len(body) - 3)
            if _DAY_RE.match(body[i])
            and _DATE_RE.match(body[i + 1])
            and _TIME_RE.match(body[i + 2])
            and _TZ_RE.match(body[i + 3])
        ]
        if starts:
            if starts[0] == 0:
                next_run = " ".join(parts[0:4])
            last_i = starts[-1]
            if not (len(starts) == 1 and starts[0] == 0 and next_run):
                last_run = " ".join(parts[last_i : last_i + 4])
                passed = " ".join(parts[last_i + 4 : -2]) or None
        timers[unit] = {
            "next": next_run,
            "last": last_run,
            "passed": passed,
        }
    return timers


def _get_failed_services():
    cfg = load_service_configs()
    failed = []
    service_names = [cfg.get(svc, {}).get("service_name", svc) for svc in SYNC_SERVICES]
    out, _, _ = _run(["systemctl", "--user", "is-failed"] + service_names)
    for svc, status in zip(SYNC_SERVICES, out.splitlines()):
        if status == "failed":
            failed.append(svc)
    return failed


def _get_service_info(name, cfg, timers=None):
    info = {"name": name, "status": "unknown", "last_run": None, "next_run": None, "details": ""}
    timer_name = cfg.get(name, {}).get("timer_name", name)
    if not timer_name.endswith(".timer"):
        timer_name = f"{timer_name}.timer"
    if timers is None:
        timers = _get_timer_status()
    if timer_name in timers:
        info["last_run"] = timers[timer_name]["last"]
        info["next_run"] = timers[timer_name]["next"]

    log_path_str = get_log_path(name, cfg)
    if log_path_str:
        log_path = Path(log_path_str)
        if log_path.exists():
            try:
                lines = log_path.read_text(errors="replace").strip().splitlines()
                tail = lines[-10:] if len(lines) > 10 else lines
                info["details"] = "\n".join(tail)
                info["log_lines"] = len(lines)
                tail_text = "\n".join(tail).lower()
                if "rsync error" in tail_text or "code 255" in tail_text:
                    info["status"] = "failed"
            except Exception:
                pass

    sync_config_path_str = get_sync_config_path(name, cfg)
    if sync_config_path_str:
        cfg_path = Path(sync_config_path_str)
        if cfg_path.exists():
            try:
                sync_cfg = json.loads(cfg_path.read_text())
                info["config"] = sync_cfg
                if "last_sync" in sync_cfg:
                    info["last_run"] = sync_cfg["last_sync"]
            except Exception:
                pass

    if name == "stokercloud-sync" and STOKERCLOUD_DB.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(STOKERCLOUD_DB))
            row = conn.execute(
                "SELECT sync_date, status, record_count FROM remote_sync_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row:
                info["last_run"] = row[0]
                info["status"] = row[1]
                info["record_count"] = row[2]
                info["details"] = f"{row[2]} records synced"
                if row[2] == 0 and row[1] == "success":
                    info["status"] = "warning"
                    info["details"] = "0 records synced (stokercloud API returned no data)"
            conn.close()
        except Exception:
            pass

    if name in info.get("failures", []) or info.get("status") == "failed":
        info["status"] = "failed"
    elif info.get("status") == "unknown" and info.get("last_run"):
        info["status"] = "completed"

    if name == "seagate-sync":
        _seagate_status_info(info)

    return info


def _get_new_files(cfg):
    result = []
    for name in SYNC_SERVICES:
        dir_str = get_watch_dir(name, cfg)
        if not dir_str:
            continue
        dir_path = Path(dir_str)
        if not dir_path.exists():
            continue
        cutoff = get_last_seen(f"scan_{name}") or (datetime.now() - timedelta(days=1)).isoformat()
        cutoff_dt = datetime.fromisoformat(cutoff)

        count = 0
        total_bytes = 0
        newest = None
        deadline = time.monotonic() + _SCAN_DEADLINE_SEC
        try:
            for f in dir_path.rglob("*"):
                if count >= _MAX_SCAN_FILES or time.monotonic() > deadline:
                    break
                if f.is_file() and f.stat().st_mtime > cutoff_dt.timestamp():
                    count += 1
                    total_bytes += f.stat().st_size
                    if newest is None or f.stat().st_mtime > newest:
                        newest = f.stat().st_mtime
        except PermissionError:
            pass

        if count > 0:
            result.append({
                "service": name,
                "directory": str(dir_path),
                "count": count,
                "total_size": _format_size(total_bytes),
            })

        set_last_seen(f"scan_{name}", datetime.now().isoformat())

    if VAULT_GIT_DIR.exists():
        out, _, _ = _run(
            ["git", "-C", str(VAULT_GIT_DIR), "log", "--since=midnight", "--oneline"],
            timeout=10,
        )
        if out:
            commits = [l for l in out.splitlines() if l.strip()]
            if commits:
                result.append({
                    "service": "grid-vault-sync",
                    "directory": "vault-git",
                    "count": len(commits),
                    "details": commits[0] if len(commits) == 1 else f"{len(commits)} commits",
                })

    return result


def _extract_news(data, cfg):
    news = []
    for fn in [_news_manga_updater, _news_portfolio_optimizer,
               _news_photo_sync, _news_snapshot_sync,
               _news_ai_wikipedia, _news_fileai_scanner,
               _news_grid_vault, _news_seagate_sync]:
        result = fn(cfg)
        if result:
            news.append(result)
    result = _news_stokercloud(data)
    if result:
        news.append(result)
    return news


def _news_grid_vault(cfg):
    out, err, rc = _run(
        ["journalctl", "--user", "-u", "grid-vault-sync.service",
         "--since=24h", "--no-pager", "--lines=20"],
        timeout=10,
    )
    if not out:
        return None
    lines = [l for l in out.splitlines() if l.strip()]
    if not lines:
        return None
    count = len(lines)
    last_line = lines[-1]
    if "No entries" in last_line or "no entries" in last_line:
        return None
    detail = f"{count} journal entries — {last_line[:80]}"
    return {"source": "grid-vault-sync", "text": detail, "icon": "📋"}


def _news_manga_updater(cfg):
    log_str = get_log_path("manga-updater", cfg)
    if not log_str:
        return None
    log = Path(log_str)
    if not log.exists():
        return None
    try:
        text = log.read_text(errors="replace")
    except Exception:
        return None

    lines = text.splitlines()
    current_name = None
    chapters = []
    up_to_date = 0
    completed = 0

    for i, line in enumerate(lines):
        stripped = _strip_log_prefix(line).strip()
        if stripped.startswith("[") and "]" in stripped:
            current_name = None
        m = re.match(r'^\s*Manga:\s+(.+)$', stripped)
        if m:
            current_name = m.group(1).strip()
        if stripped == "Up to date":
            up_to_date += 1
        if "Skipping" in stripped and "completed" in stripped:
            completed += 1
        if stripped.startswith("New:"):
            parts = stripped.split()
            count = 1
            if len(parts) >= 2:
                try:
                    count = int(parts[1])
                except ValueError:
                    count = 1
            chapter_title = ""
            if i + 1 < len(lines):
                ct_line = _strip_log_prefix(lines[i + 1]).strip()
                ct_match = re.match(r'^\[Chapter\s+([\d.]+):\s*(.*?)\]$', ct_line)
                if ct_match:
                    num = ct_match.group(1)
                    title = ct_match.group(2).strip()
                    chapter_title = f"#{num}: {title}" if title else f"#{num}"
            name = current_name or "Unknown"
            for _ in range(count):
                entry = f"{name} {chapter_title}" if chapter_title else f"{name}"
                chapters.append(entry)

    parts = []
    if chapters:
        unique = list(dict.fromkeys(chapters))
        parts.append(f"{len(unique)} new chapter{'s' if len(unique) != 1 else ''}: {', '.join(unique)}")
    if completed:
        parts.append(f"{completed} completed")
    if up_to_date:
        parts.append(f"{up_to_date} up to date")
    detail = " | ".join(parts) if parts else "No manga checked"
    return {"source": "manga-updater", "text": detail, "icon": "📚"}


def _news_portfolio_optimizer(cfg):
    log_str = get_log_path("portfolio-optimizer-sync", cfg)
    if not log_str:
        return None
    log = Path(log_str)
    if not log.exists():
        return None
    try:
        text = log.read_text(errors="replace")
    except Exception:
        return None
    lines = text.strip().splitlines()
    tail = lines[-30:] if len(lines) > 30 else lines
    tickers = 0
    for line in tail:
        if "ticker" in line.lower() and "updated" in line.lower():
            m = re.search(r"(\d+)\s+ticker", line, re.IGNORECASE)
            if m:
                tickers = int(m.group(1))
                break
        if "✓" in line:
            tickers += 1
    if tickers:
        return {"source": "portfolio-optimizer-sync", "text": f"{tickers} stock tickers updated", "icon": "📈"}
    return None


def _news_photo_sync(cfg):
    log_str = get_log_path("grid-photo-sync", cfg)
    if not log_str:
        return None
    log_path = Path(log_str)
    if not log_path.exists():
        return None
    try:
        text = log_path.read_text(errors="replace")
    except Exception:
        return None
    lines = [l for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return None
    latest = lines[-1]
    total_size = "0"
    for line in lines:
        if "total size is" in line:
            parts = line.split()
            if len(parts) >= 5:
                total_size = parts[3]
    speed = "0"
    for line in lines:
        if "speedup is" in line:
            parts = line.split()
            if len(parts) >= 3:
                speed = parts[-1]
    if total_size == "0":
        return {"source": "grid-photo-sync", "text": "No new photos (all up to date)", "icon": "🖼️"}
    return {"source": "grid-photo-sync", "text": f"Photos synced — {total_size} total, speedup {speed}", "icon": "🖼️"}


def _news_stokercloud(data):
    for svc in data.get("services", []):
        if svc["name"] == "stokercloud-sync" and svc.get("record_count"):
            return {"source": "stokercloud-sync", "text": f"{svc['record_count']} records synced to cloud", "icon": "☁️"}
    return None


def _news_snapshot_sync(cfg):
    log_str = get_log_path("snapshot-sync", cfg)
    if not log_str:
        return None
    log_path = Path(log_str)
    if not log_path.exists():
        return None
    try:
        text = log_path.read_text(errors="replace")
    except Exception:
        return None
    lines = [l for l in text.strip().splitlines() if l.strip()]
    total_size = "0"
    for line in lines:
        if "total size is" in line:
            parts = line.split()
            if len(parts) >= 5:
                total_size = parts[3]
    if total_size == "0":
        return {"source": "snapshot-sync", "text": "Snapshots synced — no changes", "icon": "💾"}
    return {"source": "snapshot-sync", "text": f"Snapshots synced — {total_size} total", "icon": "💾"}


def _news_ai_wikipedia(cfg):
    sync_config_path_str = get_sync_config_path("ai-wikipedia-sync", cfg)
    if not sync_config_path_str:
        return None
    cfg_path = Path(sync_config_path_str)
    if not cfg_path.exists():
        return None
    try:
        config = json.loads(cfg_path.read_text())
    except Exception:
        return None
    last_sync = config.get("last_sync", "unknown")
    max_articles = config.get("max_articles_per_sync", "?")
    if last_sync:
        last_sync = last_sync[:19] if len(last_sync) > 19 else last_sync
    return {"source": "ai-wikipedia-sync", "text": f"Last sync {last_sync} — up to {max_articles} articles", "icon": "📖"}


def _news_fileai_scanner(cfg):
    db_path = Path.home() / ".fileai-index.db"
    if not db_path.exists():
        return None
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        import time
        cutoff = time.time() - 86400
        row = conn.execute(
            "SELECT COUNT(*) FROM indexed_files WHERE indexed_at > ?", (cutoff,)
        ).fetchone()
        conn.close()
        count = row[0] if row else 0
    except Exception:
        count = -1
    if count < 0:
        return None
    if count == 0:
        return {"source": "fileai-scanner", "text": "No new files indexed (last 24h)", "icon": "🔍"}
    return {"source": "fileai-scanner", "text": f"{count} new files indexed in last 24h", "icon": "🔍"}


_SEAGATE_TS_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")
_LOG_PREFIX_RE = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s*")


def _strip_log_prefix(line):
    return _LOG_PREFIX_RE.sub("", line)


def _seagate_last_ts(lines):
    for line in reversed(lines):
        m = _SEAGATE_TS_RE.match(line)
        if m:
            return m.group(1)
    return None


def _seagate_status_info(info):
    log_path = Path(get_log_path("seagate-sync"))
    if not log_path.exists():
        return
    try:
        lines = [l for l in log_path.read_text(errors="replace").strip().splitlines() if l.strip()]
    except Exception:
        return
    if not lines:
        return
    last = lines[-1]
    last_ts = _seagate_last_ts(lines)
    if last_ts:
        info["last_run"] = last_ts
    if "FAILED" in last or "ERROR" in last or "could not acquire lock" in last:
        info["status"] = "failed"
    elif info.get("status") == "unknown" and last_ts:
        info["status"] = "completed"
    info["details"] = "\n".join(lines[-3:])


def _news_seagate_sync(cfg):
    log_str = get_log_path("seagate-sync", cfg)
    if not log_str:
        return None
    log_path = Path(log_str)
    if not log_path.exists():
        return None
    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except Exception:
        return None

    cutoff = (datetime.now() - timedelta(days=1)).isoformat()
    recent = [l for l in lines if l.startswith("[") and l[1:20] >= cutoff[0:19]]
    synced = sum(1 for l in recent if "DONE " in l or "[QUEUE] Queued sync OK" in l)
    failed = sum(1 for l in recent if "FAILED " in l or "[QUEUE] Queued sync FAILED" in l)
    queued = sum(1 for l in recent if "QUEUED " in l)

    pending = 0
    if _SEAGATE_QUEUE_DIR.is_dir():
        try:
            pending = sum(1 for p in _SEAGATE_QUEUE_DIR.glob("*.env"))
        except Exception:
            pending = 0

    parts = []
    if synced:
        parts.append(f"{synced} synced")
    if queued:
        parts.append(f"{queued} queued")
    if failed:
        parts.append(f"{failed} failed")
    if pending:
        parts.append(f"{pending} awaiting drain")
    if not parts:
        return None
    return {"source": "seagate-sync", "text": " | ".join(parts), "icon": "💾"}


def _compute_stats(data):
    total = len(data["services"])
    failed = len(data["failures"])
    new_files = sum(f["count"] for f in data["new_files"])
    warning_count = sum(1 for s in data["services"] if s.get("status") == "warning")
    return {
        "total_services": total,
        "failed_count": failed,
        "warning_count": warning_count,
        "ok_count": total - failed - warning_count - sum(1 for s in data["services"] if s.get("status") == "unknown"),
        "unknown_count": sum(1 for s in data["services"] if s.get("status") == "unknown"),
        "new_file_count": new_files,
    }


def _format_size(b):
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
