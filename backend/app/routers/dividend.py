"""
Dividend Calendar API Router.
Provides calendar view and upcoming dividend list, annotated with user's tracking status.
"""
import logging
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from app.database import get_supabase
from app.routers.users import get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dividend", tags=["dividend"])


def _normalize_code(symbol: str) -> str:
    """Strip exchange suffix: '2330.TW' -> '2330'."""
    return symbol.split(".")[0]


def _get_user_tracked_codes(user_id: str, sb) -> dict[str, str]:
    """Return {base_code: notify_channel} for all active tracked_indices of the user."""
    try:
        res = (
            sb.table("tracked_indices")
            .select("symbol, notify_channel")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        return {
            _normalize_code(row["symbol"]): row.get("notify_channel", "email")
            for row in (res.data or [])
        }
    except Exception as e:
        logger.warning(f"[DividendRouter] Could not fetch tracked codes for user {user_id}: {e}")
        return {}


@router.get("/calendar")
async def get_dividend_calendar(
    year: int = Query(..., description="西元年份"),
    month: int = Query(..., ge=1, le=12, description="月份 1-12"),
    authorization: str = Header(default=""),
):
    """Return all dividend events in the given month, annotated with user tracking status."""
    user_id = get_user_id(authorization)
    sb = get_supabase()

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    try:
        res = (
            sb.table("dividend_calendar")
            .select("code, name, ex_date, ex_type, cash_dividend, stock_dividend_ratio, subscription_ratio")
            .gte("ex_date", start_date.isoformat())
            .lte("ex_date", end_date.isoformat())
            .order("ex_date")
            .execute()
        )
    except Exception as e:
        logger.error(f"[DividendRouter] Calendar query failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch calendar data")

    tracked = _get_user_tracked_codes(user_id, sb)
    return [
        {
            **item,
            "is_tracked": item["code"] in tracked,
            "notify_channel": tracked.get(item["code"]),
        }
        for item in (res.data or [])
    ]


@router.get("/upcoming")
async def get_upcoming_dividends(
    days: int = Query(default=30, ge=1, le=90, description="未來天數"),
    authorization: str = Header(default=""),
):
    """Return upcoming dividend events within the next N days, annotated with tracking status."""
    user_id = get_user_id(authorization)
    sb = get_supabase()

    today = date.today()
    end_date = today + timedelta(days=days)

    try:
        res = (
            sb.table("dividend_calendar")
            .select("code, name, ex_date, ex_type, cash_dividend, stock_dividend_ratio")
            .gte("ex_date", today.isoformat())
            .lte("ex_date", end_date.isoformat())
            .order("ex_date")
            .execute()
        )
    except Exception as e:
        logger.error(f"[DividendRouter] Upcoming query failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch upcoming dividends")

    tracked = _get_user_tracked_codes(user_id, sb)
    return [
        {
            **item,
            "is_tracked": item["code"] in tracked,
            "notify_channel": tracked.get(item["code"]),
        }
        for item in (res.data or [])
    ]


@router.post("/admin/sync")
async def trigger_dividend_sync(
    background_tasks: BackgroundTasks,
    authorization: str = Header(default=""),
):
    """Admin endpoint: immediately sync dividend calendar from TWSE."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    me = sb.table("profiles").select("is_admin").eq("id", user_id).single().execute()
    if not me.data or not me.data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.services.dividend_sync import sync_dividend_calendar
    background_tasks.add_task(sync_dividend_calendar)
    return {"status": "sync_started", "message": "Dividend calendar sync started in background."}
