import structlog
import logging
import sys
from typing import Dict, Any
from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """
    Setup structured logging with structlog.
    
    Args:
        log_level: Minimum level of logs to output
        json_format: Whether to output logs in JSON format
    """
    # Configure the underlying logging library
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=getattr(logging, log_level.upper()))
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer(serializer=jsonlogger.JsonFormatter))
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                exception_formatter=structlog.dev.plain_traceback
            )
        )
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper())),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Name of the logger (defaults to current module name)
        
    Returns:
        BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context to the current thread's logger context.
    
    Args:
        **kwargs: Key-value pairs to add to the context
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """
    Remove keys from the current thread's logger context.
    
    Args:
        *keys: Keys to remove from the context
    """
    structlog.contextvars.unbind_contextvars(*keys)