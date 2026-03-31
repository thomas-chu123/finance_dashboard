"""
Public endpoints for notifications (e.g., stop alerts).
"""
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import HTMLResponse
from app.database import get_supabase

router = APIRouter(prefix="/api/public", tags=["public"])

_CONFIRM_PAGE = """
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>停止通知確認</title>
</head>
<body style="font-family: sans-serif; text-align: center; padding-top: 60px; background: #f5f5f5;">
  <div style="max-width: 420px; margin: auto; padding: 32px 24px; background: white;
              border: 1px solid #e0e0e0; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <h2 style="color: #d32f2f;">⚠️ 確認停止通知</h2>
    <p>您確定要停止 <strong>{name} ({symbol})</strong> 的價格警示通知嗎？</p>
    <p style="font-size: 0.85em; color: #888;">停止後，請登入 Dashboard 重新開啟。</p>
    <form method="post" action="/api/public/stop-notification/{tracking_id}">
      <button type="submit"
              style="background:#ef4444;color:white;border:none;padding:12px 32px;
                     border-radius:6px;font-size:15px;font-weight:bold;cursor:pointer;margin-top:8px;">
        確認停止通知
      </button>
    </form>
    <p style="margin-top:16px;">
      <a href="javascript:window.close()" style="color:#666;font-size:0.9em;">取消</a>
    </p>
  </div>
</body>
</html>
"""

_SUCCESS_PAGE = """
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>通知已停止</title>
</head>
<body style="font-family: sans-serif; text-align: center; padding-top: 60px; background: #f5f5f5;">
  <div style="max-width: 420px; margin: auto; padding: 32px 24px; background: white;
              border: 1px solid #e0e0e0; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <h2 style="color: #2e7d32;">✅ 已成功停止通知</h2>
    <p>您將不再收到有關 <strong>{name} ({symbol})</strong> 的價格觸發通知。</p>
    <p style="color: #666; font-size: 0.9em;">如果您想重新開啟，請登入 Dashboard 進行設定。</p>
  </div>
</body>
</html>
"""


@router.get("/stop-notification/{tracking_id}", response_class=HTMLResponse)
async def stop_notification_confirm(tracking_id: str):
    """
    顯示確認頁面，讓使用者主動確認後才停止通知。
    GET 僅顯示確認頁，不執行任何狀態變更，防止 email scanner 自動觸發。
    """
    sb = get_supabase()
    res = sb.table("tracked_indices").select("id, symbol, name").eq("id", tracking_id).execute()
    if not res.data:
        return HTMLResponse(
            content=f"<html><head><meta charset='utf-8'></head><body><h2>錯誤</h2><p>找不到該追蹤項目。</p></body></html>",
            status_code=404
        )
    item = res.data[0]
    return HTMLResponse(content=_CONFIRM_PAGE.format(
        name=item["name"],
        symbol=item["symbol"],
        tracking_id=tracking_id,
    ))


@router.post("/stop-notification/{tracking_id}", response_class=HTMLResponse)
async def stop_notification(tracking_id: str):
    """
    實際停止通知的端點，須由確認頁 POST 表單觸發。
    將 is_active 設為 False 並重置 alert_triggered。
    """
    sb = get_supabase()
    res = sb.table("tracked_indices").select("id, symbol, name").eq("id", tracking_id).execute()
    if not res.data:
        return HTMLResponse(
            content=f"<html><head><meta charset='utf-8'></head><body><h2>錯誤</h2><p>找不到該追蹤項目。</p></body></html>",
            status_code=404
        )
    item = res.data[0]
    try:
        sb.table("tracked_indices").update({
            "is_active": False,
            "alert_triggered": False,
        }).eq("id", tracking_id).execute()
        return HTMLResponse(content=_SUCCESS_PAGE.format(
            name=item["name"],
            symbol=item["symbol"],
        ))
    except Exception as e:
        return HTMLResponse(
            content=f"<html><head><meta charset='utf-8'></head><body><h2>系統錯誤</h2><p>{str(e)}</p></body></html>",
            status_code=500
        )
