"""Router for API v1 endpoints in Aiva AI Bot."""

from fastapi import APIRouter

from .endpoints.district_benchmarks import district_benchmarks_router
from .endpoints.market_intelligence import market_intelligence_router
from .endpoints.price_elasticity import price_elasticity_router

api_v1_router = APIRouter(prefix="/api/v1", tags=["Data API"])
api_v1_router.include_router(market_intelligence_router)
api_v1_router.include_router(price_elasticity_router)
api_v1_router.include_router(district_benchmarks_router)
