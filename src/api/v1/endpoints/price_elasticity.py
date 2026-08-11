"""Price elasticity endpoint for Aiva AI Bot."""

from fastapi import APIRouter, Depends

from ....models.api_key import APIKey
from ...deps import check_rate_limit, get_api_key

price_elasticity_router = APIRouter()


@price_elasticity_router.get("/price-elasticity")
async def get_price_elasticity(
    service_type: str,
    region: str | None = None,
    api_key: APIKey = Depends(get_api_key),
) -> dict:
    """Price elasticity data."""
    await check_rate_limit(api_key)
    return {
        "status": "coming_soon",
        "message": "Data API launching Q2 2026",
    }
