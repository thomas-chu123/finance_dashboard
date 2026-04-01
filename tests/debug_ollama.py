"""Ollama debug utility.

Usage examples:
  python tests/debug_ollama.py --show-config
  python tests/debug_ollama.py --health
  python tests/debug_ollama.py --prompt "Summarize market sentiment for VIX"
  python tests/debug_ollama.py --symbol VIX --symbol-name "CBOE VIX" --news-file tests/data/vix_news.json
  python tests/debug_ollama.py --symbol 00878 --symbol-name "Cathay ESG High Dividend" --session-hour 18
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_env() -> dict[str, str]:
    """Load KEY=VALUE pairs from common .env files."""
    env: dict[str, str] = {}
    repo_root = Path(__file__).parent.parent
    env_paths = [
        repo_root / "backend" / "app" / ".env",
        repo_root / ".env",
    ]
    for env_path in env_paths:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env.setdefault(key.strip(), value.strip())
    return env


def request_json(method: str, url: str, timeout: float, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any] | list[Any] | str]:
    """Issue an HTTP request and best-effort parse JSON response."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(text)
            except json.JSONDecodeError:
                return resp.status, text
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(text)
        except json.JSONDecodeError:
            return e.code, text


def extract_summary(payload: Any) -> str:
    """Extract model text from common Ollama response shapes."""
    def is_usable_summary(text: str) -> bool:
        normalized = re.sub(r"\s+", "", text or "")
        if len(normalized) < 80 or len(normalized) > 260:
            return False
        lowered = (text or "").lower()
        if any(k in lowered for k in ["thinking process", "source news", "return 120-180", "news 1", "**"]):
            return False
        cjk_count = len(re.findall(r"[\u4e00-\u9fff]", normalized))
        ratio = cjk_count / max(len(normalized), 1)
        return cjk_count >= 40 and ratio >= 0.45

    if not isinstance(payload, dict):
        return ""

    choices = payload.get("choices") or []
    if choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        reasoning = message.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            quoted_candidates = re.findall(r"[「\"]([^「」\"]{80,240})[」\"]", reasoning)
            for candidate in reversed(quoted_candidates):
                text = candidate.strip()
                if is_usable_summary(text):
                    return text
            sentence_candidates = re.findall(r"([\u4e00-\u9fff0-9A-Za-z，。；：、（）\(\)\-]{90,260}[。！？])", reasoning)
            for candidate in reversed(sentence_candidates):
                text = candidate.strip()
                if is_usable_summary(text):
                    return text
        if isinstance(content, list):
            merged = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            ).strip()
            if merged:
                return merged
        text = first.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

    response_text = payload.get("response")
    if isinstance(response_text, str) and response_text.strip():
        return response_text.strip()

    message = payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        reasoning = message.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning.strip()

    return ""


def build_market_prompt(symbol: str, symbol_name: str, session_hour: int, news_items: list[dict[str, Any]]) -> str:
    """Build a market-summary style prompt similar to production flow."""
    session_map = {8: "pre-open briefing", 13: "midday update", 18: "after-close briefing"}
    session_label = session_map.get(session_hour, "market update")

    if not news_items:
        news_items = [
            {"title": f"{symbol} latest market move", "description": "No external news injected for debug run."},
            {"title": f"{symbol} sentiment watch", "description": "Use this placeholder to validate model output shape."},
        ]

    blocks: list[str] = []
    for i, item in enumerate(news_items[:5], start=1):
        title = str(item.get("title") or "(no title)")
        desc = str(item.get("description") or "(no description)")
        blocks.append(f"News {i}: {title}\nDetails: {desc}")

    joined = "\n\n".join(blocks)
    return (
        f"You are a financial analyst. Create a Traditional Chinese summary for {symbol_name} ({symbol}) "
        f"for the {session_label}.\n\n"
        f"Source news:\n{joined}\n\n"
        "Return 120-180 Chinese characters and cover: main development, possible impact, what investors should watch."
    )


def load_news_items(news_file: str | None) -> list[dict[str, Any]]:
    """Load news list from JSON file if provided."""
    if not news_file:
        return []
    path = Path(news_file)
    if not path.exists():
        print(f"[ERROR] news file not found: {news_file}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("news_items"), list):
        return [x for x in data["news_items"] if isinstance(x, dict)]
    print("[ERROR] news file must be a list of objects or {'news_items': [...]}", file=sys.stderr)
    sys.exit(1)


def print_config(base_url: str, model: str, timeout: float) -> None:
    print("\n=== Ollama Debug Config ===\n")
    print(f"  base_url : {base_url}")
    print(f"  model    : {model}")
    print(f"  timeout  : {timeout}s")
    print()


def run_health_checks(base_url: str, timeout: float, model: str) -> int:
    """Run lightweight Ollama health checks and print diagnostics."""
    failed = 0

    status, payload = request_json("GET", f"{base_url}/api/tags", timeout)
    print(f"[health] GET /api/tags -> {status}")
    if status >= 400:
        failed += 1
    else:
        model_names: list[str] = []
        if isinstance(payload, dict):
            for item in payload.get("models", []):
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str):
                        model_names.append(name)
        print(f"         models found: {len(model_names)}")
        if model_names:
            print(f"         first models: {', '.join(model_names[:5])}")
            if not any(model in m for m in model_names):
                print(f"         [warn] target model '{model}' not found in /api/tags list")

    status2, payload2 = request_json("GET", f"{base_url}/v1/models", timeout)
    print(f"[health] GET /v1/models -> {status2}")
    if status2 >= 400:
        failed += 1
    else:
        count = 0
        if isinstance(payload2, dict) and isinstance(payload2.get("data"), list):
            count = len(payload2["data"])
        print(f"         v1 models count: {count}")

    return failed


def run_chat(
    base_url: str,
    model: str,
    timeout: float,
    prompt: str,
    temperature: float,
    max_tokens: int,
    think: bool | None,
    raw: bool,
) -> int:
    """Call /api/chat once and print parsed output."""
    if think is False and "qwen" in model.lower() and not prompt.lstrip().startswith("/no_think"):
        prompt = f"/no_think\n{prompt}"

    if think is None:
        think = False

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": think,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    started = time.perf_counter()
    status, response_payload = request_json("POST", f"{base_url}/api/chat", timeout, body=payload)
    elapsed = time.perf_counter() - started

    print(f"\n[chat] POST /api/chat -> {status} ({elapsed:.2f}s)")
    if status >= 400:
        print("[error] request failed")
        if isinstance(response_payload, (dict, list)):
            print(json.dumps(response_payload, ensure_ascii=False, indent=2)[:1200])
        else:
            print(str(response_payload)[:1200])
        return 1

    summary = extract_summary(response_payload)
    finish_reason = ""
    if isinstance(response_payload, dict):
        choices = response_payload.get("choices") or []
        if choices and isinstance(choices[0], dict):
            finish_reason = str(choices[0].get("finish_reason") or "")
        if not finish_reason:
            finish_reason = str(response_payload.get("done_reason") or "")
    print(f"[chat] extracted chars: {len(summary)}")
    if finish_reason:
        print(f"[chat] finish_reason: {finish_reason}")
    if summary:
        print("\n=== Extracted Output ===\n")
        print(summary)
    else:
        print("\n[warn] No extractable content found from response payload")

    if raw:
        print("\n=== Raw Response (truncated) ===\n")
        if isinstance(response_payload, (dict, list)):
            print(json.dumps(response_payload, ensure_ascii=False, indent=2)[:3000])
        else:
            print(str(response_payload)[:3000])

    return 0


def main() -> None:
    env = load_env()

    parser = argparse.ArgumentParser(description="Debug Ollama connectivity and response parsing")
    parser.add_argument("--show-config", action="store_true", help="Show effective config and exit")
    parser.add_argument("--health", action="store_true", help="Run /api/tags and /v1/models health checks")
    parser.add_argument("--prompt", default=None, help="Direct prompt for one-shot chat test")
    parser.add_argument("--symbol", default=None, help="Symbol for market-summary style prompt")
    parser.add_argument("--symbol-name", default=None, help="Display name for symbol")
    parser.add_argument("--session-hour", type=int, default=8, help="Session hour label (8/13/18)")
    parser.add_argument("--news-file", default=None, help="Path to JSON file with news items")
    parser.add_argument("--base-url", default=env.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"), help="Ollama base URL")
    parser.add_argument("--model", default=env.get("OLLAMA_MODEL", "gpt-oss:20b"), help="Model name")
    parser.add_argument("--temperature", type=float, default=0.3, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, default=400, help="Max output tokens")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout seconds")
    parser.add_argument("--think", choices=["auto", "on", "off"], default="off", help="Set Ollama think mode")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON response")
    args = parser.parse_args()

    print_config(args.base_url, args.model, args.timeout)
    if args.show_config and not (args.health or args.prompt or args.symbol):
        return

    exit_code = 0

    if args.health:
        exit_code = max(exit_code, run_health_checks(args.base_url, args.timeout, args.model))

    prompt = args.prompt
    if args.symbol:
        symbol_name = args.symbol_name or args.symbol
        news_items = load_news_items(args.news_file)
        prompt = build_market_prompt(args.symbol, symbol_name, args.session_hour, news_items)
        print(f"\n[info] market prompt built for {args.symbol} ({symbol_name}), news={len(news_items) if news_items else 0}")
    elif prompt is None and not args.health:
        prompt = "Reply with one Traditional Chinese sentence to confirm this Ollama model works."

    if prompt is not None:
        print("\n=== Prompt Preview (first 400 chars) ===\n")
        print(prompt[:400])
        think_value = None
        if args.think == "on":
            think_value = True
        elif args.think == "off":
            think_value = False
        exit_code = max(
            exit_code,
            run_chat(
                base_url=args.base_url,
                model=args.model,
                timeout=args.timeout,
                prompt=prompt,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                think=think_value,
                raw=args.raw,
            ),
        )

    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
