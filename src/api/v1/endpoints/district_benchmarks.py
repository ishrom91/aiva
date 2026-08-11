"""District benchmarks endpoint for Aiva AI Bot."""

from fastapi import APIRouter, Depends

from ....models.api_key import APIKey
from ...deps import check_rate_limit, get_api_key

district_benchmarks_router = APIRouter()


@district_benchmarks_router.get("/district-benchmarks")
async def get_district_benchmarks(
    district: str,
    api_key: APIKey = Depends(get_api_key),
) -> dict:
    """District benchmark data."""
    await check_rate_limit(api_key)
    return {
        "status": "coming_soon",
        "message": "Data API launching Q2 2026",
    }
