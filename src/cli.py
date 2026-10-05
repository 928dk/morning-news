#!/usr/bin/env python3
"""Morning News CLI — update, show JSON, or serve."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collector import collect
from src.summarizer import summarize
from src.db import save_report, get_latest_report
from src.config import CACHE_DIR, REPORT_PATH


def cmd_update():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = collect()
    llm_summary = summarize(data)
    data["summary"] = llm_summary
    save_report(data, llm_summary)
    REPORT_PATH.write_text(json.dumps(data, indent=2, default=str))
    print(f"Morning news updated: {len(data.get('services', []))} services, "
          f"{len(data.get('failures', []))} failures, "
          f"{len(data.get('new_files', []))} new file groups")
    print(f"Summary: {llm_summary[:120]}...")
    return 0


def cmd_json():
    if REPORT_PATH.exists():
        print(REPORT_PATH.read_text())
    else:
        print(json.dumps({"error": "No report yet — run --update first"}))
    return 0


def cmd_serve(access_log=False):
    import http.server
    import socketserver
    PORT = 8787
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(CACHE_DIR), **kw)

        if not access_log:
            def log_message(self, fmt, *args):
                pass

    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Morning News HTTP serving at http://127.0.0.1:{PORT}/report.json")
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Morning News — sync status collector")
    parser.add_argument("--update", action="store_true", help="Collect data and generate report")
    parser.add_argument("--json", action="store_true", help="Print latest report as JSON")
    parser.add_argument("--serve", action="store_true", help="Serve report.json via HTTP")
    parser.add_argument("--access-log", action="store_true", help="Enable HTTP access log (with --serve)")
    args = parser.parse_args()

    if args.update:
        return cmd_update()
    elif args.json:
        return cmd_json()
    elif args.serve:
        return cmd_serve(access_log=args.access_log)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
