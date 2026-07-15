from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..utils.logger import get_logger
import uuid
import time


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests with structured logging.
    Adds request_id, timing info, and basic request/response details.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Log incoming request
        self.logger.info(
            "Incoming request",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else None,
            client_port=request.client.port if request.client else None,
        )
        
        # Add request ID to request state for other handlers to use
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
        except Exception as e:
            # Log the error
            processing_time = time.time() - start_time
            self.logger.error(
                "Request failed with exception",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                processing_time_ms=round(processing_time * 1000, 2),
                error=str(e),
                exc_info=True
            )
            raise
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log the response
        self.logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            processing_time_ms=round(processing_time * 1000, 2),
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


def setup_logging_middleware(app):
    """
    Helper function to add logging middleware to FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(LoggingMiddleware)