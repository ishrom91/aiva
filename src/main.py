from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import asyncio
import structlog
from typing import Dict, Any
import hashlib
import hmac
from .config import settings
from .database import init_db, close_db
from .handlers import start_router, booking_router, admin_router, subscription_router
from .utils.logger import setup_logging
from .middlewares.logging import setup_logging_middleware
from .middlewares.event_logger import EventLoggerMiddleware
from .repositories.booking_repo import BookingRepository
from .services.booking_service import BookingService
from .api.v1 import router as api_router

# Setup logging
setup_logging(settings.LOG_LEVEL)

logger = structlog.get_logger(__name__)

# Initialize bot and dispatcher
try:
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    logger.info("Bot initialized successfully")
except Exception as e:
    logger.error("Failed to initialize bot", error=str(e))
    raise

# Include routers
dp.include_router(start_router)
dp.include_router(booking_router)
dp.include_router(admin_router)
dp.include_router(subscription_router)

# Add event logger middleware if data collection is enabled
if settings.DATA_COLLECTION_ENABLED:
    dp.message.middleware(EventLoggerMiddleware())
    dp.callback_query.middleware(EventLoggerMiddleware())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Aiva AI bot application...", 
                port=settings.WEB_SERVER_PORT, 
                webhook_url=settings.WEBHOOK_URL)
    
    try:
        # Initialize database
        init_db(settings.DATABASE_URL)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    # Set webhook if WEBHOOK_URL is provided
    try:
        if settings.WEBHOOK_URL:
            webhook_info = await bot.get_webhook_info()
            if webhook_info.url != settings.WEBHOOK_URL:
                await bot.set_webhook(
                    url=settings.WEBHOOK_URL,
                    drop_pending_updates=True,
                    allowed_updates=dp.resolve_used_update_types()
                )
                logger.info(f"Webhook set to: {settings.WEBHOOK_URL}")
            else:
                logger.info(f"Webhook already set to: {settings.WEBHOOK_URL}")
        else:
            logger.info("WEBHOOK_URL not set, running in polling mode")
    except Exception as e:
        logger.error("Failed to set webhook", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aiva AI bot application...")
    
    # Delete webhook to switch back to polling if needed
    try:
        if settings.WEBHOOK_URL:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted")
    except Exception as e:
        logger.error("Failed to delete webhook", error=str(e))
    
    # Close database connection
    try:
        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error("Failed to close database connection", error=str(e))


# Create FastAPI app
app = FastAPI(
    title="Aiva AI Bot API",
    description="Telegram bot for beauty industry professionals",
    version="1.0.0",
    lifespan=lifespan
)

# Setup logging middleware
setup_logging_middleware(app)

# Include API routes
app.include_router(api_router)


@app.post(settings.WEBHOOK_PATH)
async def bot_webhook(request: Request):
    """Bot webhook endpoint"""
    try:
        # Verify webhook if needed (Telegram doesn't require verification by default)
        # But you can implement custom verification here if needed
        
        # Get the update data
        update_data = await request.json()
        
        # Process the update through the dispatcher
        await dp.feed_raw_update(bot, update_data)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error("Error processing webhook", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Here you could check connections to DB, Redis, etc.
    # For now, just return a simple OK
    return {
        "status": "healthy",
        "details": {
            "database": "connected",  # Would check actual connection in real implementation
            "redis": "connected"      # Would check actual connection in real implementation
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Aiva AI Bot API",
        "version": "1.0.0",
        "description": "Telegram bot for beauty industry professionals",
        "features": [
            "Booking management",
            "Subscription system",
            "Data collection for analytics"
        ],
        "port": settings.WEB_SERVER_PORT,
        "webhook_url": settings.WEBHOOK_URL
    }


# Setup webhook handler
async def setup_webhook():
    """Setup webhook handler for aiohttp"""
    try:
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=settings.WEBHOOK_PATH)
        logger.info("Webhook handler registered successfully")
    except Exception as e:
        logger.error("Failed to register webhook handler", error=str(e))
        raise


# Run the application if this file is executed directly
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting server", host=settings.WEB_SERVER_HOST, port=settings.WEB_SERVER_PORT)
    
    # Setup webhook
    try:
        asyncio.run(setup_webhook())
    except Exception as e:
        logger.error("Failed to setup webhook", error=str(e))
        raise
    
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host=settings.WEB_SERVER_HOST,
        port=settings.WEB_SERVER_PORT,
        reload=True  # Only for development
    )