import json
import requests
from .config import OLLAMA_URL, OLLAMA_MODEL, APP_CONFIG_PATH


def _get_model():
    if APP_CONFIG_PATH.exists():
        try:
            cfg = json.loads(APP_CONFIG_PATH.read_text())
            return cfg.get("ollama_model", OLLAMA_MODEL)
        except Exception:
            pass
    return OLLAMA_MODEL


def summarize(data: dict) -> str:
    prompt = _build_prompt(data)
    model = _get_model()
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"num_predict": 300},
            },
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json()["message"]["content"].strip()
    except Exception as e:
        pass
    return _fallback_summary(data)


def _build_prompt(data):
    services = data.get("services", [])
    failures = data.get("failures", [])
    new_files = data.get("new_files", [])
    news_items = data.get("news", [])
    stats = data.get("summary_stats", {})

    parts = ["You are a helpful assistant. Summarize this morning's sync status in 2-3 short paragraphs:"]
    parts.append(f"Total services: {stats.get('total_services', 0)}")
    parts.append(f"Failed: {stats.get('failed_count', 0)}")
    parts.append(f"OK: {stats.get('ok_count', 0)}")

    if failures:
        parts.append(f"Failed services: {', '.join(failures)}")

    if news_items:
        parts.append("\nService activity:")
        for item in news_items:
            parts.append(f"- {item['source']}: {item['text']}")

    for svc in services:
        if svc.get("status") == "failed":
            parts.append(f"- {svc['name']}: FAILED ({svc.get('details', '')[:100]})")
        elif svc.get("last_run"):
            parts.append(f"- {svc['name']}: last run {svc['last_run']}")

    if new_files:
        parts.append("New files:")
        for nf in new_files:
            size_info = nf.get("total_size", "")
            if size_info:
                parts.append(f"  - {nf['directory']}: {nf['count']} files ({size_info})")
            else:
                parts.append(f"  - {nf['directory']}: {nf['count']} items")

    if failures:
        parts.append("\nHighlight any failed services and suggest action.")
    else:
        parts.append("\nAll clear if nothing failed.")

    return "\n".join(parts)


def _fallback_summary(data):
    failures = data.get("failures", [])
    new_files = data.get("new_files", [])
    stats = data.get("summary_stats", {})
    parts = []
    if failures:
        parts.append(f"⚠ {len(failures)} service(s) failed: {', '.join(failures)}")
    else:
        parts.append(f"✓ All {stats.get('total_services', 0)} sync services completed")
    if new_files:
        parts.append(f"📁 {stats.get('new_file_count', 0)} new file(s): " +
                     ", ".join(f"{f['directory']} ({f['count']})" for f in new_files))
    return " | ".join(parts) if parts else "No data yet"
