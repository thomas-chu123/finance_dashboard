"""
AI 每日市場早報 API 路由.
提供：GET /latest、GET /sessions、POST /trigger
"""
import logging
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from app.database import get_supabase
from app.routers.users import get_user_id
from app.services.news_briefing_service import run_market_briefing_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("/latest")
async def get_latest_briefing(authorization: str = Header(default="")):
    """
    取得最新一次排程批次中，屬於目前使用者追蹤清單的 symbol 早報摘要.

    Returns:
        {"session_time": str, "items": [...]}
    """
    user_id = get_user_id(authorization)
    sb = get_supabase()

    # 1. 查出該使用者追蹤的 is_active symbol 集合
    try:
        tracking_res = (
            sb.table("tracked_indices")
            .select("symbol")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
    except Exception as e:
        logger.error(f"[Briefing API] 查詢 tracked_indices 失敗: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

    user_symbols = {row["symbol"] for row in (tracking_res.data or [])}
    if not user_symbols:
        return {"session_time": None, "items": []}

    # 2. 一次查詢取最近 50 筆 briefing（含 session_time），再從最新 session 過濾並只保留使用者追蹤的 symbols
    try:
        items_res = (
            sb.table("market_briefings")
            .select("session_time, symbol, symbol_name, summary_text, news_json, status, error_message")
            .order("session_time", desc=True)
            .order("symbol")
            .limit(50)
            .execute()
        )
    except Exception as e:
        logger.error(f"[Briefing API] 查詢 market_briefings 失敗: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

    if not items_res.data:
        return {"session_time": None, "items": []}

    session_time = items_res.data[0]["session_time"]
    items = [
        r for r in items_res.data
        if r["session_time"] == session_time and r["symbol"] in user_symbols
    ]

    return {
        "session_time": session_time,
        "items": items,
    }


@router.get("/sessions")
async def get_briefing_sessions(authorization: str = Header(default="")):
    """
    取得最近 10 次排程清單（含每次完成 symbol 數）.

    Returns:
        [{"session_time": str, "total": int, "completed": int, "failed": int}, ...]
    """
    get_user_id(authorization)
    sb = get_supabase()

    try:
        res = (
            sb.table("market_briefings")
            .select("session_time, status")
            .order("session_time", desc=True)
            .limit(200)  # 最多 10 session × 20 symbols
            .execute()
        )
    except Exception as e:
        logger.error(f"[Briefing API] 查詢 sessions 失敗: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

    # 按 session_time 分組統計
    sessions: dict[str, dict] = {}
    for row in (res.data or []):
        st = row["session_time"]
        if st not in sessions:
            sessions[st] = {"session_time": st, "total": 0, "completed": 0, "failed": 0}
        sessions[st]["total"] += 1
        if row["status"] == "completed":
            sessions[st]["completed"] += 1
        elif row["status"] == "failed":
            sessions[st]["failed"] += 1

    result = sorted(sessions.values(), key=lambda x: x["session_time"], reverse=True)[:10]
    return result


@router.post("/trigger", status_code=202)
async def trigger_briefing(
    background_tasks: BackgroundTasks,
    authorization: str = Header(default=""),
):
    """
    手動觸發一次市場早報排程（背景非同步執行）.
    供開發測試使用，需要 JWT 認證.

    Returns:
        {"status": "triggered", "message": str}
    """
    get_user_id(authorization)
    background_tasks.add_task(run_market_briefing_session)
    logger.info("[Briefing API] 手動觸發排程")
    return {
        "status": "triggered",
        "message": "市場早報排程已在背景啟動，請稍後透過 GET /api/briefing/latest 查看結果",
    }
