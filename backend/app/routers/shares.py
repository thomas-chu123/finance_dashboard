"""投組分享路由 - 支援快照快享和實時公開投組。"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Header, Query
from app.database import get_supabase
from app.config import get_settings
from app.models import (
    PortfolioShareRequest,
    PortfolioShareResponse,
    PublicPortfolioShareResponse,
    UserShareListResponse,
    ShareArchiveRequest,
)
from app.routers.users import get_user_id
from app.utils.share_utils import generate_share_key, validate_share_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/backtest", tags=["shares"])


# ──────────────────────────────────────────────────────────────────────
# Private: Create Share (Authenticated)
# ──────────────────────────────────────────────────────────────────────
@router.post("/portfolio/{portfolio_id}/share", response_model=PortfolioShareResponse)
async def create_portfolio_share(
    portfolio_id: str,
    body: PortfolioShareRequest,
    authorization: str = Header(default=""),
):
    """為投組建立分享快照。
    
    傳入投組 ID，生成短碼和快照數據。
    快照一旦建立就不再變更（immutable）。
    
    Args:
        portfolio_id: 投組 UUID
        body: 分享請求（share_type, expires_in_days, description）
        authorization: JWT token
        
    Returns:
        分享信息（短碼、URL、過期時間等）
        
    Raises:
        404: 投組不存在或不屬於用戶
        409: 短碼碰撞（極少發生）
    """
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    logger.info(f"📋 建立分享: portfolio={portfolio_id}, user={user_id}")
    
    # 1. 驗證投組是否存在且屬於用戶
    try:
        portfolio = (
            sb.table("backtest_portfolios")
            .select("*, backtest_portfolio_items(*)")
            .eq("id", portfolio_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except Exception as e:
        logger.warning(f"⚠️  投組不存在或無權限: {e}")
        raise HTTPException(status_code=404, detail="Portfolio not found or access denied")
    
    portfolio_data = portfolio.data
    
    # 2. 準備快照數據
    portfolio_snapshot = {
        "id": portfolio_data["id"],
        "name": portfolio_data["name"],
        "portfolio_type": portfolio_data.get("portfolio_type", "backtest"),
        "initial_amount": portfolio_data["initial_amount"],
        "start_date": portfolio_data.get("start_date"),
        "end_date": portfolio_data.get("end_date"),
        "results_json": portfolio_data.get("results_json"),
        "created_at": portfolio_data["created_at"],
    }
    
    portfolio_items_snapshot = [
        {
            "symbol": item["symbol"],
            "name": item.get("name"),
            "weight": item["weight"],
            "category": item.get("category"),
        }
        for item in portfolio_data.get("backtest_portfolio_items", [])
    ]
    
    # 3. 生成短碼
    share_key = generate_share_key()
    
    # 4. 計算過期時間
    expires_at = None
    if body.expires_in_days and body.expires_in_days > 0:
        expires_at = (datetime.utcnow() + timedelta(days=body.expires_in_days)).isoformat()
    elif body.share_type == "snapshot":
        # 快照預設 30 天過期
        expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    
    # 5. 建立分享記錄
    share_data = {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "share_key": share_key,
        "share_type": body.share_type,
        "is_public": True,  # 預設公開
        "is_archived": False,
        "portfolio_snapshot": portfolio_snapshot,
        "portfolio_items_snapshot": portfolio_items_snapshot,
        "expires_at": expires_at,
    }
    
    try:
        result = sb.table("portfolio_shares").insert(share_data).execute()
        share = result.data[0]
        logger.info(f"✅ 分享已建立: share_key={share_key}")
    except Exception as e:
        logger.error(f"❌ 建立分享失敗: {e}")
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=409, detail="Share key collision (please try again)")
        raise HTTPException(status_code=500, detail="Failed to create share")
    
    # 6. 生成分享 URL（使用環境變數的 APP_BASE_URL）
    settings = get_settings()
    share_url = f"{settings.app_base_url}/share/{share_key}"
    
    return PortfolioShareResponse(
        id=share["id"],
        share_key=share["share_key"],
        share_url=share_url,
        share_type=share["share_type"],
        is_public=share["is_public"],
        is_archived=share["is_archived"],
        expires_at=share.get("expires_at"),
        view_count=share.get("view_count", 0),
        share_count=share.get("share_count", 0),
        created_at=share["created_at"],
    )


# ──────────────────────────────────────────────────────────────────────
# Public: View Share (No Authentication)
# ──────────────────────────────────────────────────────────────────────
@router.get("/share/{share_key}", response_model=PublicPortfolioShareResponse)
async def get_public_share(share_key: str):
    """取得公開分享的投組數據（無需認證）。
    
    Args:
        share_key: 分享短碼
        
    Returns:
        公開分享的投組數據
        
    Raises:
        404: 分享不存在或已過期
        410: 分享已被刪除或存檔
    """
    if not validate_share_key(share_key):
        logger.warning(f"⚠️  無效的短碼格式: {share_key}")
        raise HTTPException(status_code=400, detail="Invalid share key format")
    
    sb = get_supabase()
    
    logger.info(f"📖 查詢分享: {share_key}")
    
    try:
        result = (
            sb.table("portfolio_shares")
            .select("*")
            .eq("share_key", share_key)
            .eq("is_public", True)
            .is_("is_archived", "false")  # 排除已存檔
            .single()
            .execute()
        )
        share = result.data
    except Exception as e:
        logger.warning(f"⚠️  分享不存在: {e}")
        raise HTTPException(status_code=404, detail="Share not found or not public")
    
    # 驗證過期時間
    if share.get("expires_at"):
        expires_at = datetime.fromisoformat(share["expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow() > expires_at.replace(tzinfo=None):
            logger.info(f"⏰ 分享已過期: {share_key}")
            raise HTTPException(status_code=410, detail="Share has expired")
    
    # 異步更新 view_count（不阻塞回應）
    try:
        sb.table("portfolio_shares").update({
            "view_count": (share.get("view_count", 0) or 0) + 1,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", share["id"]).execute()
    except Exception as e:
        logger.warning(f"⚠️  更新瀏覽計數失敗: {e}")
    
    # 組織回應（隱藏敏感信息）
    portfolio_data = share.get("portfolio_snapshot", {})
    
    return PublicPortfolioShareResponse(
        share_key=share["share_key"],
        portfolio=portfolio_data,
        shared_by=None,  # 匿名分享
        created_at=share["created_at"],
        view_count=share.get("view_count", 0) + 1,
    )


# ──────────────────────────────────────────────────────────────────────
# Private: List User's Shares
# ──────────────────────────────────────────────────────────────────────
@router.get("/shares", response_model=list[UserShareListResponse])
async def list_user_shares(
    authorization: str = Header(default=""),
    portfolio_id: Optional[str] = Query(None),
    is_archived: Optional[bool] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|view_count)$"),
):
    """列出用戶的所有分享。
    
    Args:
        authorization: JWT token
        portfolio_id: 篩選特定投組的分享
        is_archived: 篩選存檔狀態
        sort_by: 排序欄位（created_at 或 view_count）
        
    Returns:
        用戶分享列表
    """
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    logger.info(f"📋 列表分享: user={user_id}")
    
    # 建立查詢
    query = sb.table("portfolio_shares").select(
        "*, backtest_portfolios(name, portfolio_type)"
    ).eq("user_id", user_id)
    
    # 應用篩選
    if portfolio_id:
        query = query.eq("portfolio_id", portfolio_id)
    if is_archived is not None:
        query = query.eq("is_archived", is_archived)
    
    # 排序
    desc = sort_by == "created_at"  # 預設按建立時間倒序
    query = query.order(sort_by, desc=desc)
    
    try:
        result = query.execute()
        shares = result.data or []
    except Exception as e:
        logger.error(f"❌ 查詢分享失敗: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch shares")
    
    # 轉換回應格式
    settings = get_settings()
    response = []
    for share in shares:
        portfolio = share.get("backtest_portfolios", {})
        share_url = f"{settings.app_base_url}/share/{share['share_key']}"
        
        response.append(
            UserShareListResponse(
                share_key=share["share_key"],
                portfolio_id=share["portfolio_id"],
                portfolio_name=portfolio.get("name", "Unknown"),
                portfolio_type=portfolio.get("portfolio_type", "backtest"),
                view_count=share.get("view_count", 0),
                share_count=share.get("share_count", 0),
                is_public=share["is_public"],
                is_archived=share["is_archived"],
                expires_at=share.get("expires_at"),
                created_at=share["created_at"],
                share_url=share_url,
            )
        )
    
    return response


# ──────────────────────────────────────────────────────────────────────
# Private: Delete Share
# ──────────────────────────────────────────────────────────────────────
@router.delete("/shares/{share_key}")
async def delete_share(share_key: str, authorization: str = Header(default="")):
    """刪除分享（永久刪除）。
    
    Args:
        share_key: 分享短碼
        authorization: JWT token
        
    Returns:
        { "status": "deleted" }
        
    Raises:
        404: 分享不存在
        403: 無權刪除（不是所有者）
    """
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    if not validate_share_key(share_key):
        raise HTTPException(status_code=400, detail="Invalid share key format")
    
    logger.info(f"🗑️  刪除分享: {share_key}, user={user_id}")
    
    # 驗證所有權
    try:
        share = (
            sb.table("portfolio_shares")
            .select("id, user_id")
            .eq("share_key", share_key)
            .single()
            .execute()
        )
    except Exception as e:
        logger.warning(f"⚠️  分享不存在: {e}")
        raise HTTPException(status_code=404, detail="Share not found")
    
    if share.data["user_id"] != user_id:
        logger.warning(f"⚠️  無權刪除分享: user={user_id}, owner={share.data['user_id']}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this share")
    
    # 刪除分享
    try:
        sb.table("portfolio_shares").delete().eq("id", share.data["id"]).execute()
        logger.info(f"✅ 分享已刪除: {share_key}")
    except Exception as e:
        logger.error(f"❌ 刪除分享失敗: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete share")
    
    return {"status": "deleted"}


# ──────────────────────────────────────────────────────────────────────
# Private: Archive Share
# ──────────────────────────────────────────────────────────────────────
@router.patch("/shares/{share_key}")
async def archive_share(
    share_key: str,
    body: ShareArchiveRequest,
    authorization: str = Header(default=""),
):
    """存檔或恢復分享（隱藏但不刪除）。
    
    Args:
        share_key: 分享短碼
        body: 存檔狀態請求
        authorization: JWT token
        
    Returns:
        { "is_archived": bool, "updated_at": str }
        
    Raises:
        404: 分享不存在
        403: 無權編輯（不是所有者）
    """
    user_id = get_user_id(authorization)
    sb = get_supabase()
    
    if not validate_share_key(share_key):
        raise HTTPException(status_code=400, detail="Invalid share key format")
    
    logger.info(f"📦 存檔狀態更新: {share_key}, archived={body.is_archived}")
    
    # 驗證所有權
    try:
        share = (
            sb.table("portfolio_shares")
            .select("id, user_id")
            .eq("share_key", share_key)
            .single()
            .execute()
        )
    except Exception as e:
        logger.warning(f"⚠️  分享不存在: {e}")
        raise HTTPException(status_code=404, detail="Share not found")
    
    if share.data["user_id"] != user_id:
        logger.warning(f"⚠️  無權編輯分享: user={user_id}, owner={share.data['user_id']}")
        raise HTTPException(status_code=403, detail="Not authorized to edit this share")
    
    # 更新存檔狀態
    try:
        result = sb.table("portfolio_shares").update({
            "is_archived": body.is_archived,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", share.data["id"]).execute()
        
        updated = result.data[0]
        logger.info(f"✅ 分享已更新: archived={updated['is_archived']}")
    except Exception as e:
        logger.error(f"❌ 更新分享失敗: {e}")
        raise HTTPException(status_code=500, detail="Failed to update share")
    
    return {
        "is_archived": updated["is_archived"],
        "updated_at": updated["updated_at"],
    }
