"""Portfolio templates router."""
import logging
from fastapi import APIRouter, HTTPException, Header
from app.services.portfolio_template_service import get_all_templates
from app.security import get_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/portfolio-templates", tags=["pt"])

@router.get("/available")
async def get_templates():
    try:
        t = get_all_templates()
        return {"data": t}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
