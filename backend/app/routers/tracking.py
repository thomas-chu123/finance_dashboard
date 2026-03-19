"""Index tracking CRUD router."""
from fastapi import APIRouter, HTTPException, Header
from app.models import TrackingCreate, TrackingUpdate, TrackingResponse, AddFromBacktestRequest
from app.database import get_supabase
from app.routers.users import get_user_id

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.get("", response_model=list[TrackingResponse])
async def list_tracking(authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    res = sb.table("tracked_indices").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data or []


@router.post("", response_model=TrackingResponse)
async def create_tracking(body: TrackingCreate, authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    data = body.model_dump()
    data["user_id"] = user_id
    res = sb.table("tracked_indices").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Create failed")
    return res.data[0]


@router.put("/{tracking_id}", response_model=TrackingResponse)
async def update_tracking(tracking_id: str, body: TrackingUpdate, authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    res = (
        sb.table("tracked_indices")
        .update(update_data)
        .eq("id", tracking_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Tracking not found")
    return res.data[0]


@router.delete("/{tracking_id}")
async def delete_tracking(tracking_id: str, authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    sb.table("tracked_indices").delete().eq("id", tracking_id).eq("user_id", user_id).execute()
    return {"message": "Deleted successfully"}


@router.post("/from-backtest")
async def add_from_backtest(body: AddFromBacktestRequest, authorization: str = Header(default="")):
    """One-click add ETFs from backtest results into tracking."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    created = []
    for symbol, name, category in zip(body.symbols, body.names, body.categories):
        # Skip if already tracked
        existing = (
            sb.table("tracked_indices")
            .select("id")
            .eq("user_id", user_id)
            .eq("symbol", symbol)
            .execute()
        )
        if existing.data:
            continue
        data = {
            "user_id": user_id,
            "symbol": symbol,
            "name": name,
            "category": category,
            "is_active": True,
        }
        res = sb.table("tracked_indices").insert(data).execute()
        if res.data:
            created.append(res.data[0])
    return {"message": f"Added {len(created)} tracking entries", "created": created}


@router.get("/alerts")
async def get_alert_logs(authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    res = (
        sb.table("alert_logs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return res.data or []
