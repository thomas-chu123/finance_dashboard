"""LINE Message API notification service."""
import httpx
from app.config import get_settings

settings = get_settings()
LINE_MESSAGE_API_URL = "https://api.line.me/v2/bot/message/push"


async def send_line_message(user_id: str, message: str) -> dict:
    if not settings.line_channel_access_token:
        return {"success": False, "error": "No LINE token configured"}
    if not user_id:
        return {"success": False, "error": "No LINE user_id provided"}

    headers = {
        "Authorization": f"Bearer {settings.line_channel_access_token}",
        "Content-Type": "application/json",
    }
    payload = {"to": user_id, "messages": [{"type": "text", "text": message}]}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(LINE_MESSAGE_API_URL, headers=headers, json=payload)
            success = resp.status_code == 200
            print(f"[LINE] Send {'OK' if success else 'FAILED'}: {resp.status_code}")
            return {
                "success": success,
                "http_status": resp.status_code,
                "error": None if success else resp.text[:200],
            }
        except Exception as e:
            print(f"[LINE] Exception: {e}")
            return {"success": False, "error": str(e)}


def _build_rsi_condition_label(
    current_rsi: float | None,
    rsi_below: float | None,
    rsi_above: float | None,
) -> str:
    """根據當前 RSI 值與閾值，產生精確的 RSI 觸發條件描述。"""
    if rsi_below is not None and rsi_above is not None:
        # 若能判斷哪個觸發則優先顯示已觸發的那個
        if current_rsi is not None and current_rsi < rsi_below:
            return f"RSI 閥值跌破 {rsi_below:.0f}"
        if current_rsi is not None and current_rsi > rsi_above:
            return f"RSI 閥值突破 {rsi_above:.0f}"
        return f"RSI 閥值跌破 {rsi_below:.0f} 或突破 {rsi_above:.0f}"
    if rsi_below is not None:
        return f"RSI 閥值跌破 {rsi_below:.0f}"
    if rsi_above is not None:
        return f"RSI 閥值突破 {rsi_above:.0f}"
    return "RSI 觸發"


def _build_trigger_condition_label(
    trigger_direction: str,
    trigger_price: float | None,
    trigger_mode: str,
    current_rsi: float | None,
    rsi_below: float | None,
    rsi_above: float | None,
) -> str:
    """產生完整觸發條件描述，依 trigger_mode 組合價格與 RSI 條件。"""
    price_dir = "突破" if trigger_direction == "above" else "跌破"
    price_label = f"價格{price_dir} {trigger_price:.2f}" if trigger_price is not None else ""
    rsi_label = _build_rsi_condition_label(current_rsi, rsi_below, rsi_above)

    if trigger_mode == "price":
        return price_label
    if trigger_mode == "rsi":
        return rsi_label
    if trigger_mode == "both":
        return f"{price_label} 及 {rsi_label}"
    if trigger_mode == "either":
        return f"{price_label} 或 {rsi_label}"
    return price_label


def build_alert_message(
    symbol: str,
    name: str,
    current_price: float,
    trigger_price: float,
    trigger_direction: str,
    tracking_id: str,
    trigger_mode: str = "price",
    current_rsi: float | None = None,
    rsi_below: float | None = None,
    rsi_above: float | None = None,
) -> str:
    arrow = "🔺" if trigger_direction == "above" else "🔻"

    trigger_condition = _build_trigger_condition_label(
        trigger_direction, trigger_price, trigger_mode,
        current_rsi, rsi_below, rsi_above
    )

    # RSI 信息行（可選）
    rsi_line = ""
    if current_rsi is not None:
        if current_rsi < (rsi_below or 30):
            rsi_signal = "⚠️ 超賣信號"
        elif current_rsi > (rsi_above or 70):
            rsi_signal = "⚠️ 超買信號"
        else:
            rsi_signal = "✅ 正常範圍"
        rsi_line = f"📈 RSI (14)：{current_rsi:.2f} {rsi_signal}\n"

    mode_desc = {
        "price": "價格",
        "rsi": "RSI 指標",
        "both": "價格及 RSI",
        "either": "價格或 RSI",
    }.get(trigger_mode, "價格")

    return (
        f"\n📊 {mode_desc}觸發通知\n"
        f"━━━━━━━━━━━━━\n"
        f"📌 代碼：{symbol}\n"
        f"📋 名稱：{name}\n"
        f"🎯 觸發條件：{trigger_condition}\n"
        f"{arrow} 目前價格：{current_price:.2f}\n"
        f"{rsi_line}"
        f"━━━━━━━━━━━━━\n"
        f"請登入 Finance Dashboard 查看更多資訊。\n\n"
        f"停止此項通知：\n"
        f"{settings.backend_base_url}/api/public/stop-notification/{tracking_id}"
    )

