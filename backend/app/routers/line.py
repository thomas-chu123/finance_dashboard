"""LINE Messaging API router."""
from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import random
import string
from datetime import datetime, timedelta
import logging

from app.database import get_supabase
from app.config import get_settings
from app.routers.users import get_user_id
from app.services.line_service import send_line_message

router = APIRouter(prefix="/api/line", tags=["line"])
settings = get_settings()
logger = logging.getLogger(__name__)

class LineEvent(BaseModel):
    type: str
    replyToken: Optional[str] = None
    source: dict
    message: Optional[dict] = None

class LineWebhookRequest(BaseModel):
    events: List[dict]

@router.post("/binding-code")
async def generate_binding_code(authorization: str = Header(default="")):
    """Generate a 6-digit binding code for the current user and return bot info."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    # Generate 6 random digits
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
    
    # Save to profile
    try:
        res = sb.table("profiles").update({
            "line_binding_code": code,
            "line_binding_expires_at": expires_at
        }).eq("id", user_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to save binding code")
            
        return {
            "code": code, 
            "expires_at": expires_at,
            "bot_id": settings.line_bot_user_id
        }
    except Exception as e:
        logger.error(f"Error generating binding code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def line_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle LINE Messaging API webhook."""
    # Note: Signature validation should be added here in production
    
    body = await request.json()
    events = body.get("events", [])
    
    for event in events:
        event_type = event.get("type")
        source = event.get("source", {})
        line_user_id = source.get("userId")
        
        if not line_user_id:
            continue
            
        if event_type == "follow":
            background_tasks.add_task(
                send_line_message, 
                line_user_id, 
                "歡迎使用投資通知系統！請在網頁端生成「綁定碼」，並在此輸入 `bind 123456` 來連結您的帳號。"
            )
            
        elif event_type == "message":
            msg = event.get("message", {})
            if msg.get("type") == "text":
                text = msg.get("text", "").strip()
                if text.lower().startswith("bind"):
                    parts = text.split()
                    if len(parts) == 2:
                        code = parts[1]
                        background_tasks.add_task(handle_binding, line_user_id, code)
    
    return {"status": "ok"}

async def handle_binding(line_user_id: str, code: str):
    """Link LINE user ID to account using binding code."""
    sb = get_supabase()
    now = datetime.now().isoformat()
    
    # 1. Find user with this code and not expired
    res = sb.table("profiles").select("id").eq("line_binding_code", code).gt("line_binding_expires_at", now).execute()
    
    if not res.data:
        await send_line_message(line_user_id, "❌ 綁定碼無效或已過期，請重新生成。")
        return
        
    user_id = res.data[0]["id"]
    
    # 2. Update profile with line_user_id and clear code
    update_res = sb.table("profiles").update({
        "line_user_id": line_user_id,
        "line_binding_code": None,
        "line_binding_expires_at": None,
        "notify_line": True
    }).eq("id", user_id).execute()
    
    if update_res.data:
        await send_line_message(line_user_id, "✅ 帳號綁定成功！您現在將會透過 LINE 收到投資提醒。")
    else:
        await send_line_message(line_user_id, "❌ 綁定失敗，系統發生錯誤。")
