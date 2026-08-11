import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..utils.logger import get_logger


class AivaLoggingMiddleware(BaseHTTPMiddleware):
    """HTTP request logging middleware for FastAPI."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger = get_logger(__name__)
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "Incoming request",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else None,
        )

        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as exc:
            processing_time = time.time() - start_time
            logger.error(
                "Request failed with exception",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                processing_time_ms=round(processing_time * 1000, 2),
                error=str(exc),
                exc_info=True,
            )
            raise

        processing_time = time.time() - start_time
        logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            processing_time_ms=round(processing_time * 1000, 2),
        )
        response.headers["X-Request-ID"] = request_id
        return response


def setup_logging_middleware(app) -> None:
    """Add Aiva logging middleware to the FastAPI app."""
    app.add_middleware(AivaLoggingMiddleware)
