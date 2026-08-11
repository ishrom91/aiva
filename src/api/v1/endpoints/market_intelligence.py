"""Market intelligence endpoint for Aiva AI Bot."""

from fastapi import APIRouter, Depends

from ....models.api_key import APIKey
from ...deps import check_rate_limit, get_api_key

market_intelligence_router = APIRouter()


@market_intelligence_router.get("/market-intelligence")
async def get_market_intelligence(
    region: str | None = None,
    service_category: str | None = None,
    time_range: str = "last_30_days",
    api_key: APIKey = Depends(get_api_key),
) -> dict:
    """Demand trends by service."""
    await check_rate_limit(api_key)
    return {
        "status": "coming_soon",
        "message": "Data API launching Q2 2026",
        "example_response": {
            "demand_trend": {
                "manicure_hardware": "+23%",
                "manicure_classic": "-15%",
            }
        },
    }
