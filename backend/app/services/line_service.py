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
) -> str:
    direction_label = "突破" if trigger_direction == "above" else "跌破"
    arrow = "🔺" if trigger_direction == "above" else "🔻"
    return (
        f"\n📊 投資價格觸發通知\n"
        f"━━━━━━━━━━━━━\n"
        f"📌 代碼：{symbol}\n"
        f"📋 名稱：{name}\n"
        f"🎯 觸發條件：{direction_label} {trigger_price}\n"
        f"{arrow} 目前價格：{current_price}\n"
        f"━━━━━━━━━━━━━\n"
        f"請登入 Finance Dashboard 查看更多資訊。\n\n"
        f"停止此項通知：\n"
        f"{settings.backend_base_url}/api/public/stop-notification/{tracking_id}"
    )
