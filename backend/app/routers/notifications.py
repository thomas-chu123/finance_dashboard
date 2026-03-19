"""
Public endpoints for notifications (e.g., stop alerts).
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.database import get_supabase

router = APIRouter(prefix="/api/public", tags=["public"])

@router.get("/stop-notification/{tracking_id}", response_class=HTMLResponse)
async def stop_notification(tracking_id: str):
    """
    Public endpoint to stop notifications for a given tracked index.
    Disables the alert by setting is_active = false.
    """
    sb = get_supabase()
    
    # Check if exists
    res = sb.table("tracked_indices").select("id, symbol, name").eq("id", tracking_id).execute()
    if not res.data:
        return HTMLResponse(content=f"<html><body><h2>錯誤</h2><p>找不到該追蹤項目 (ID: {tracking_id})。</p></body></html>", status_code=404)
        
    item = res.data[0]
    
    # Update is_active to false
    try:
        sb.table("tracked_indices").update({
            "is_active": False,
            "alert_triggered": False,
        }).eq("id", tracking_id).execute()
        
        return HTMLResponse(content=f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <div style="max-width: 400px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2e7d32;">✅ 已成功停止通知</h2>
                <p>您將不再收到有關 <strong>{item['name']} ({item['symbol']})</strong> 的價格觸發通知。</p>
                <p style="color: #666; font-size: 0.9em;">如果您想重新開啟，請登入 Dashboard 進行設定。</p>
            </div>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h2>系統錯誤</h2><p>{str(e)}</p></body></html>", status_code=500)
