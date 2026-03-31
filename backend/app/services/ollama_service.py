"""
Ollama Direct API 摘要服務 — 取代 gemini_service.

端點：http://192.168.0.26:11434/api/chat
認證：無（Ollama Direct 不需要認證）
模型：gpt-oss:20b（由 OLLAMA_MODEL 環境變數控制）

注意：此服務直連內網 Ollama 實例，不透過 OpenWebUI proxy。
後端伺服器必須與 192.168.0.26 在同一網段才能存取。
"""
import logging
import re
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
OLLAMA_REQUEST_RETRIES = 2

SESSION_LABEL_MAP = {
    8: "開盤前早報",
    13: "午間快報",
    18: "收盤後晚報",
}


def _clean_text(value: str, limit: int) -> str:
    """清理摘要輸入文字，移除多餘空白與常見搜尋噪訊。"""
    text = (value or "").strip()
    if not text:
        return ""
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text)
    # 常見搜尋頁噪訊關鍵字
    text = text.replace("快照", "")
    text = text.replace("›", " ")
    text = re.sub(r"\s+", " ", text).strip(" -|:")
    return text[:limit]


def _prepare_news_items(news_items: list[dict]) -> list[dict]:
    """標準化 SearXNG 新聞資料，避免空描述或過長文本影響 LLM 輸出。"""
    prepared: list[dict] = []
    seen_urls: set[str] = set()

    for item in news_items:
        if not isinstance(item, dict):
            continue
        url = (item.get("url") or "").strip()
        if not url or url in seen_urls:
            continue

        title = _clean_text(str(item.get("title") or ""), 160)
        desc_raw = str(item.get("description") or "")
        description = _clean_text(desc_raw, 280)
        if not description:
            description = title

        if not title:
            continue

        seen_urls.add(url)
        prepared.append(
            {
                "title": title,
                "description": description,
                "url": url,
                "published_date": item.get("published_date") or "",
            }
        )
    return prepared


def _extract_summary_from_payload(payload: dict) -> str:
    """從多種回應格式中提取摘要文字。"""

    def _is_usable_summary(text: str) -> bool:
        normalized = re.sub(r"\s+", "", text or "")
        if len(normalized) < 80 or len(normalized) > 260:
            return False
        # 排除常見推理/提示詞雜訊
        lowered = (text or "").lower()
        noise_keywords = ["thinking process", "source news", "return 120-180", "news 1", "**"]
        if any(k in lowered for k in noise_keywords):
            return False
        cjk_count = len(re.findall(r"[\u4e00-\u9fff]", normalized))
        ratio = cjk_count / max(len(normalized), 1)
        return cjk_count >= 40 and ratio >= 0.45
    # 舊版 chat/completions 類型格式（相容解析）
    choices = payload.get("choices") or []
    if choices:
        first = choices[0] or {}
        message = first.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        # qwen3.* 可能把推理內容放在 reasoning，最終答案仍可能出現在其中
        reasoning = message.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            # 優先抓取推理中已組好的繁中摘要（常見於 gpt-oss/qwen 只回 reasoning）
            quoted_candidates = re.findall(r"[「\"]([^「」\"]{80,240})[」\"]", reasoning)
            for candidate in reversed(quoted_candidates):
                text = candidate.strip()
                if _is_usable_summary(text):
                    return text

            sentence_candidates = re.findall(r"([\u4e00-\u9fff0-9A-Za-z，。；：、（）\(\)\-]{90,260}[。！？])", reasoning)
            for candidate in reversed(sentence_candidates):
                text = candidate.strip()
                if _is_usable_summary(text):
                    return text

            for marker in ("Final Answer:", "Final answer:", "最終答案：", "最終答案:"):
                idx = reasoning.rfind(marker)
                if idx != -1:
                    candidate = reasoning[idx + len(marker):].strip()
                    if candidate:
                        return candidate
        # 某些模型/代理可能回 content list
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

    # Ollama /api/generate 常見格式
    response_text = payload.get("response")
    if isinstance(response_text, str) and response_text.strip():
        return response_text.strip()

    # Ollama /api/chat 格式
    message = payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        reasoning = message.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning.strip()

    return ""


def _fallback_summary(symbol_name: str, news_items: list[dict]) -> str:
    """當 LLM 回空或失敗時，以新聞標題組成簡短繁中摘要。"""
    if not news_items:
        return ""

    titles = [
        (item.get("title") or "").strip()
        for item in news_items[:3]
        if (item.get("title") or "").strip()
    ]
    if not titles:
        return ""

    joined_titles = "；".join(titles)
    summary = (
        f"{symbol_name} 近期市場焦點集中在：{joined_titles}。"
        "整體訊息顯示短線波動仍高，建議關注事件後續發展與成交量變化，"
        "並搭配風險控管與分批布局。"
    )
    # 控制長度，避免過長影響下游顯示
    return summary[:220]


def _build_prompt(
    symbol: str,
    symbol_name: str,
    news_items: list[dict],
    session_label: str,
) -> str:
    """建立送給 Ollama 的摘要 Prompt（英文指令 + 繁中輸出要求）."""
    news_blocks = []
    for i, item in enumerate(news_items, start=1):
        title = item.get("title", "（無標題）")
        description = item.get("description", "（無描述）")
        news_blocks.append(f"News {i}: {title}\nDetails: {description}")

    news_text = "\n\n".join(news_blocks)
    return (
        f"You are a financial analyst. Create a Traditional Chinese summary for "
        f"{symbol_name} ({symbol}) for the {session_label}.\n\n"
        f"Source news:\n{news_text}\n\n"
        "Return 120-180 Chinese characters and cover: main development, possible impact, what investors should watch. "
        "Output plain text only in Traditional Chinese."
    )


def _build_retry_prompt(symbol: str, symbol_name: str, news_items: list[dict], session_label: str) -> str:
    """第二次重試用的精簡 Prompt（與已驗證樣式一致）."""
    bullets = []
    for i, item in enumerate(news_items[:3], start=1):
        bullets.append(
            f"News {i}: {item.get('title', '（無標題）')}\n"
            f"Details: {item.get('description', '（無描述）')}"
        )
    lines = "\n\n".join(bullets)
    return (
        f"You are a financial analyst. Write a Traditional Chinese summary for {symbol_name} ({symbol}) "
        f"for the {session_label}.\n\n"
        f"Source news:\n{lines}\n\n"
        "Return 120-180 Chinese characters. Include market move, likely impact, and watch points. "
        "Output plain text only."
    )


def _with_no_think_directive(prompt: str) -> str:
    """在提示詞前加上 qwen 系列可識別的 no_think 指令。"""
    stripped = prompt.lstrip()
    if stripped.startswith("/no_think"):
        return prompt
    return f"/no_think\n{prompt}"


async def _post_chat(base_url: str, payload: dict) -> httpx.Response:
    """送出 Ollama chat request，針對瞬斷做少量重試。"""
    last_err: Exception | None = None
    for attempt in range(1, OLLAMA_REQUEST_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                return await client.post(
                    f"{base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
        except Exception as exc:
            last_err = exc
            logger.warning(f"[Ollama] request attempt={attempt} failed: {exc}")
            if attempt >= OLLAMA_REQUEST_RETRIES:
                break
    if last_err:
        raise last_err
    raise RuntimeError("Unexpected Ollama request state")


async def generate_market_summary(
    symbol: str,
    symbol_name: str,
    news_items: list[dict],
    session_hour: int = 8,
) -> str:
    """
    呼叫 Ollama gpt-oss:20b 生成繁體中文市場摘要.

    Args:
        symbol: 股票/ETF 代碼（例如 "VTI"）
        symbol_name: 中文名稱（例如 "先鋒整體市場ETF"）
        news_items: 由 searxng_service.search_news 回傳的新聞 list
        session_hour: 排程小時（8/13/18），用於 prompt 標籤

    Returns:
        100-150 字繁體中文摘要字串；失敗時回傳空字串 ""

    Examples:
        >>> summary = await generate_market_summary("VTI", "先鋒整體市場ETF", news_items, 8)
        >>> # "美股市場今日開盤前..."
    """
    settings = get_settings()
    base_url = settings.ollama_base_url
    model = settings.ollama_model
    simple_prompt_first = settings.ollama_simple_prompt_first

    if not base_url:
        logger.warning("[Ollama] ollama_base_url 未設定，跳過摘要生成")
        return ""
    prepared_news_items = _prepare_news_items(news_items)
    if not prepared_news_items:
        logger.info(f"[Ollama] {symbol} 無新聞，跳過摘要生成")
        return ""

    session_label = SESSION_LABEL_MAP.get(session_hour, "市場快報")
    if simple_prompt_first:
        prompt = _build_retry_prompt(symbol, symbol_name, prepared_news_items, session_label)
    else:
        prompt = _build_prompt(symbol, symbol_name, prepared_news_items, session_label)
    is_qwen_family = "qwen" in (model or "").lower()
    if is_qwen_family:
        prompt = _with_no_think_directive(prompt)

    # 使用 Ollama /api/chat；固定關閉 think 與 stream
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 400,
        },
    }

    try:
        # timeout=120s：20B 模型首次推理（冷啟動）可能需要 60-90s
        resp = await _post_chat(base_url=base_url, payload=payload)

        if resp.status_code != 200:
            logger.error(f"[Ollama] HTTP {resp.status_code} for {symbol}: {resp.text[:200]}")
            fallback = _fallback_summary(symbol_name, news_items)
            if fallback:
                logger.warning(f"[Ollama] {symbol} 改用 fallback 摘要（HTTP 非 200）")
            return fallback

        payload_json = resp.json()
        summary = _extract_summary_from_payload(payload_json)
        if not summary:
            logger.warning(
                f"[Ollama] {symbol} 首次回應無可用文字，payload_head={str(payload_json)[:600]}"
            )
            # 精簡 Prompt 再試一次，避免模型因輸入噪訊回空內容
            retry_prompt = (
                _build_prompt(symbol, symbol_name, prepared_news_items, session_label)
                if simple_prompt_first
                else _build_retry_prompt(symbol, symbol_name, prepared_news_items, session_label)
            )
            choices = payload_json.get("choices") or []
            finish_reason = ""
            if choices and isinstance(choices[0], dict):
                finish_reason = str(choices[0].get("finish_reason") or "").lower()
            if not finish_reason:
                finish_reason = str(payload_json.get("done_reason") or "").lower()

            # qwen 系列常見：content 空 + reasoning 長文 + finish_reason=length
            # 改用 no_think 指令再試一次，避免 token 全耗在推理。
            if is_qwen_family and finish_reason == "length":
                retry_prompt = _with_no_think_directive(retry_prompt)
            retry_payload = {
                "model": model,
                "messages": [{"role": "user", "content": retry_prompt}],
                "stream": False,
                "think": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 320,
                },
            }
            retry_resp = await _post_chat(base_url=base_url, payload=retry_payload)
            if retry_resp.status_code == 200:
                retry_json = retry_resp.json()
                retry_summary = _extract_summary_from_payload(retry_json)
                if retry_summary:
                    logger.info(f"[Ollama] {symbol} 重試後摘要生成成功（{len(retry_summary)} 字）")
                    return retry_summary
                logger.warning(
                    f"[Ollama] {symbol} 重試仍無可用文字，payload_head={str(retry_json)[:600]}"
                )

            logger.warning(f"[Ollama] {symbol} 回應無可用文字，改用 fallback 摘要")
            return _fallback_summary(symbol_name, prepared_news_items)

        logger.info(f"[Ollama] {symbol} 摘要生成成功（{len(summary)} 字）")
        return summary

    except Exception as e:
        logger.error(f"[Ollama] 摘要生成失敗 symbol={symbol}: {e}")
        fallback = _fallback_summary(symbol_name, prepared_news_items)
        if fallback:
            logger.warning(f"[Ollama] {symbol} 例外後改用 fallback 摘要")
        return fallback
