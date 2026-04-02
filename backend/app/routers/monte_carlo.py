from fastapi import APIRouter, HTTPException, Header
from app.models import MonteCarloRequest, MonteCarloResponse
from app.routers.users import get_user_id
from app.services.monte_carlo_engine import run_monte_carlo_simulation
from fastapi_cache.decorator import cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monte-carlo", tags=["monte-carlo"])

@router.post("/run", response_model=MonteCarloResponse)
@cache(expire=3600)
async def run_monte_carlo_endpoint(body: MonteCarloRequest, authorization: str = Header(default="")):
    """
    Run a Monte Carlo simulation.
    Requires user authentication.
    """
    get_user_id(authorization) # Validate auth
    
    if not body.assets:
        raise HTTPException(status_code=400, detail="At least one asset is required")
    
    total_weight = sum(a.weight for a in body.assets)
    if abs(total_weight - 1.0) > 0.01:
        # We'll allow it but the engine will normalize it. 
        # However, it's better to warn or error if it's way off.
        pass

    assets_list = [a.model_dump() for a in body.assets]
    
    try:
        result = await run_monte_carlo_simulation(
            assets=assets_list,
            initial_amount=body.initial_amount,
            years=body.years,
            simulations=body.simulations,
            annual_contribution=body.annual_contribution,
            annual_withdrawal=body.annual_withdrawal,
            inflation_mean=body.inflation_mean,
            inflation_std=body.inflation_std,
            adjust_for_inflation=body.adjust_for_inflation
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
    except Exception as e:
        logger.error(f"Monte Carlo simulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")
