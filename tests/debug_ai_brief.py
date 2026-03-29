"""AI Briefing Debug Tool — 手動觸發 / 查看 AI 早報結果.

使用方式：
  cd finance_dashboard

  # 觸發排程並等候 60 秒後顯示結果
  python tests/debug_ai_brief.py --trigger

  # 觸發並只等 30 秒
  python tests/debug_ai_brief.py --trigger --wait 30

  # 只顯示最新早報（不觸發）
  python tests/debug_ai_brief.py --latest

  # 列出最近 session 清單
  python tests/debug_ai_brief.py --sessions

  # 指定帳密（否則自動讀 .env 中的 DEBUG_EMAIL / DEBUG_PASSWORD）
  python tests/debug_ai_brief.py --trigger --email me@example.com --password secret
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8005"


def _request(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict:
    url = BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print("[ERROR] HTTP %d: %s" % (e.code, e.read().decode()[:300]), file=sys.stderr)
        sys.exit(1)


def login(email: str, password: str) -> str:
    print("  -> Login %s ..." % email)
    result = _request("POST", "/api/auth/login", body={"email": email, "password": password})
    token = result.get("access_token") or result.get("token")
    if not token:
        print("[ERROR] Login failed: %s" % result, file=sys.stderr)
        sys.exit(1)
    print("  OK")
    return token


def _load_env_credentials() -> tuple[str | None, str | None]:
    email = password = None
    env_paths = [
        Path(__file__).parent.parent / "backend" / "app" / ".env",
        Path(__file__).parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("DEBUG_EMAIL="):
                    email = email or line.split("=", 1)[1].strip()
                elif line.startswith("DEBUG_PASSWORD="):
                    password = password or line.split("=", 1)[1].strip()
    return email, password


def print_latest(data: dict) -> None:
    session_time = data.get("session_time")
    items = data.get("items", [])
    if not session_time:
        print("\n[!] No briefing records (run migration or trigger first)")
        return
    print("\n=== Latest Briefing  session=%s  symbols=%d ===\n" % (session_time, len(items)))
    print("  %-14s %-22s %-10s %s" % ("SYMBOL", "NAME", "STATUS", "SUMMARY (60 chars)"))
    print("  " + "-" * 100)
    for item in items:
        symbol = item.get("symbol", "")
        name = (item.get("symbol_name") or "")[:20]
        status = item.get("status", "")
        summary = (item.get("summary_text") or item.get("error_message") or "(none)")[:60]
        news_cnt = len(item.get("news_json") or [])
        icon = "[OK]" if status == "completed" else ("[NG]" if status == "failed" else "[..]")
        print("  %-14s %-22s %s %-9s %s  [%d news]" % (symbol, name, icon, status, summary, news_cnt))


def print_sessions(sessions: list) -> None:
    print("\n=== Recent %d sessions ===\n" % len(sessions))
    print("  %-32s %6s %10s %7s" % ("session_time", "total", "completed", "failed"))
    print("  " + "-" * 62)
    for s in sessions:
        print("  %-32s %6d %10d %7d" % (
            s["session_time"], s["total"], s["completed"], s["failed"]
        ))


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Briefing Debug Tool")
    parser.add_argument("--trigger",  action="store_true", help="Manually trigger briefing session")
    parser.add_argument("--latest",   action="store_true", help="Show latest briefing result")
    parser.add_argument("--sessions", action="store_true", help="List recent sessions")
    parser.add_argument("--wait", type=int, default=60,
                        help="Seconds to wait after trigger before showing result (default: 60)")
    parser.add_argument("--email",    default=None, help="Login email")
    parser.add_argument("--password", default=None, help="Login password")
    args = parser.parse_args()

    # 未指定動作時，預設顯示最新早報
    if not (args.trigger or args.latest or args.sessions):
        args.latest = True

    email = args.email
    password = args.password
    if not email or not password:
        env_email, env_pass = _load_env_credentials()
        email = email or env_email
        password = password or env_pass
    if not email or not password:
        print(
            "[ERROR] Provide --email/--password, or set DEBUG_EMAIL/DEBUG_PASSWORD in .env",
            file=sys.stderr,
        )
        sys.exit(1)

    token = login(email, password)

    if args.sessions:
        sessions = _request("GET", "/api/briefing/sessions", token=token)
        print_sessions(sessions)

    if args.trigger:
        print("\n[*] Triggering briefing session...")
        resp = _request("POST", "/api/briefing/trigger", token=token, body={})
        print("  -> " + resp.get("message", str(resp)))
        if args.wait > 0:
            print("\n  [*] Waiting %ds for background job..." % args.wait)
            for elapsed in range(0, args.wait, 5):
                remaining = args.wait - elapsed
                print("      ~%ds remaining..." % remaining, end="\r", flush=True)
                time.sleep(min(5, remaining))
            print()
        args.latest = True

    if args.latest:
        data = _request("GET", "/api/briefing/latest", token=token)
        print_latest(data)


if __name__ == "__main__":
    main()
