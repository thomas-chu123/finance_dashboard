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
    direction_label = "突破" if trigger_direction == "above" else "跌破"
    arrow = "🔺" if trigger_direction == "above" else "🔻"
    
    # RSI 信息行（可選）
    rsi_line = ""
    if current_rsi is not None:
        rsi_signal = ""
        if current_rsi < 30:
            rsi_signal = "⚠️ 超賣信號"
        elif current_rsi > 70:
            rsi_signal = "⚠️ 超買信號"
        else:
            rsi_signal = "✅ 正常範圍"
        
        rsi_line = f"📈 RSI (14)：{current_rsi:.2f} {rsi_signal}\n"
        if rsi_below is not None and rsi_above is not None:
            rsi_line += f"   閾值：超賣 {rsi_below:.0f} / 超買 {rsi_above:.0f}\n"
    
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
        f"🎯 觸發條件：{direction_label} {trigger_price:.2f}\n"
        f"{arrow} 目前價格：{current_price:.2f}\n"
        f"{rsi_line}"
        f"━━━━━━━━━━━━━\n"
        f"請登入 Finance Dashboard 查看更多資訊。\n\n"
        f"停止此項通知：\n"
        f"{settings.backend_base_url}/api/public/stop-notification/{tracking_id}"
    )

