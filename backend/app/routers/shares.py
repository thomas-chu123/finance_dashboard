"""圖形分享路由 - 提供 PNG 圖形的上傳與無認證讀取功能。"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Form, UploadFile, File
from fastapi.responses import FileResponse
from app.routers.users import get_user_id
from app.services.image_share import ImageShareManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/backtest", tags=["shares"])
image_manager = ImageShareManager()


# ──────────────────────────────────────────────────────────────────────
# Public: Get Shared Image (Unauthenticated)
# ──────────────────────────────────────────────────────────────────────
@router.get("/share/image/{image_hash}")
async def get_shared_image(image_hash: str):
    """獲取無認證分享的PNG圖形"""
    try:
        image_path = image_manager.get_image(image_hash)
        return FileResponse(
            image_path,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except FileNotFoundError as e:
        logger.warning(f"⚠️  圖像未找到: {image_hash} - {e}")
        raise HTTPException(status_code=404, detail="Image not found or expired")
    except Exception as e:
        logger.error(f"❌ 獲取圖像失敗: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve image")


# ──────────────────────────────────────────────────────────────────────
# Private: Upload Result Image (Authenticated)
# ──────────────────────────────────────────────────────────────────────
@router.post("/share/image/upload")
async def upload_result_image(
    file: UploadFile = File(...),
    result_type: str = Form(..., description="圖形類型: backtest, optimize, monte_carlo"),
    portfolio_id: Optional[str] = Form(None, description="投組ID"),
    authorization: str = Header(None),
):
    """上傳回測/優化/蒙地卡羅結果PNG圖形"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_id = get_user_id(authorization)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        if result_type not in ["backtest", "optimize", "monte_carlo"]:
            raise HTTPException(status_code=400, detail="Invalid result_type")

        content = await file.read()

        image_hash = image_manager.generate_image_hash(
            portfolio_id=portfolio_id or user_id,
            result_type=result_type,
        )

        image_manager.save_image(
            image_data=content,
            image_hash=image_hash,
            result_type=result_type,
            user_id=user_id,
        )

        logger.info(f"✅ 圖像已保存: {image_hash} (類型: {result_type})")

        return {
            "image_hash": image_hash,
            "result_type": result_type,
            "share_url": f"/share/image/{image_hash}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 上傳圖像失敗: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")
