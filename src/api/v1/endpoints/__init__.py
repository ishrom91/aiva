"""API v1 endpoints package for Aiva AI Bot."""

from .district_benchmarks import district_benchmarks_router
from .market_intelligence import market_intelligence_router
from .price_elasticity import price_elasticity_router

__all__ = [
    "market_intelligence_router",
    "price_elasticity_router",
    "district_benchmarks_router",
]
