from fastapi import APIRouter, Depends, HTTPException
from ..deps import get_api_key, check_rate_limit

router = APIRouter(prefix="/v1", tags=["Data API"])

@router.get("/market-intelligence")
async def market_intelligence(
    region: str = None,
    service_category: str = None,
    time_range: str = "last_30_days",
    api_key = Depends(get_api_key)
):
    """Demand trends by service"""
    await check_rate_limit(api_key)
    return {
        "status": "coming_soon",
        "message": "Data API launching Q2 2026",
        "example_response": {
            "demand_trend": {
                "manicure_hardware": "+23%",
                "manicure_classic": "-15%"
            }
        }
    }

@router.get("/price-elasticity")
async def price_elasticity(
    service_type: str,
    region: str = None,
    api_key = Depends(get_api_key)
):
    """Price elasticity"""
    await check_rate_limit(api_key)
    return {
        "status": "coming_soon",
        "message": "Data API launching Q2 2026"
    }

@router.get("/district-benchmarks")
async def district_benchmarks(
    district: str,
    api_key = Depends(get_api_key)
):
    """District benchmarks"""
    await check_rate_limit(api_key)
    return {
        "status": "coming_soon",
        "message": "Data API launching Q2 2026"
    }