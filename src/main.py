import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .api.v1 import api_v1_router
from .config import settings
from .database import close_db, engine, init_db
from .handlers import ALL_ROUTERS
from .middlewares.event_logger import EventLoggerMiddleware
from .middlewares.master_context import MasterContextMiddleware
from .utils.logger import setup_logging


def create_bot() -> Bot:
    """Create Bot with explicit Telegram API server and optional HTTP/SOCKS proxy."""
    session = (
        AiohttpSession(proxy=settings.TELEGRAM_PROXY)
        if settings.TELEGRAM_PROXY
        else AiohttpSession()
    )
    return Bot(
        token=settings.BOT_TOKEN,
        session=session,
        server=TelegramAPIServer(
            base="https://api.telegram.org",
            file="https://api.telegram.org/file/bot",
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    setup_logging(settings.LOG_LEVEL)
    logger = structlog.get_logger(__name__)

    await init_db(settings.DATABASE_URL)

    if not settings.REDIS_URL:
        storage: MemoryStorage | RedisStorage = MemoryStorage()
        logger.warning("dev mode: MemoryStorage")
    else:
        redis_connection = redis.from_url(settings.REDIS_URL)
        storage = RedisStorage(redis=redis_connection)

    bot = create_bot()
    dispatcher = Dispatcher(storage=storage)

    for router in ALL_ROUTERS:
        dispatcher.include_router(router)

    dispatcher.update.middleware(MasterContextMiddleware())
    dispatcher.update.outer_middleware(EventLoggerMiddleware())

    app.state.polling_task = None

    if settings.WEBHOOK_URL:
        try:
            current_webhook_info = await bot.get_webhook_info()
            if current_webhook_info.url != settings.WEBHOOK_URL:
                await bot.set_webhook(
                    url=settings.WEBHOOK_URL,
                    secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
                    drop_pending_updates=True,
                )
        except Exception as exc:
            logger.warning("Could not configure webhook", error=str(exc))
    else:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception as exc:
            logger.warning("Could not delete webhook before polling", error=str(exc))
        logger.info("WEBHOOK_URL not set — starting polling mode")
        app.state.polling_task = asyncio.create_task(
            dispatcher.start_polling(bot, handle_signals=False)
        )

    app.state.bot = bot
    app.state.dp = dispatcher

    yield

    if app.state.polling_task is not None:
        app.state.polling_task.cancel()
        try:
            await app.state.polling_task
        except asyncio.CancelledError:
            pass

    if settings.WEBHOOK_URL:
        await bot.delete_webhook()

    await bot.session.close()
    await close_db()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root() -> dict:
    return {"status": "ok", "service": "Aiva AI Bot", "version": "1.0.0"}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint - ping Redis + DB."""
    db_ok = False
    redis_ok = False

    try:
        if engine:
            async with AsyncSession(engine) as session:
                await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    try:
        if settings.REDIS_URL:
            redis_client = redis.from_url(settings.REDIS_URL)
            await redis_client.ping()
            await redis_client.aclose()
            redis_ok = True
        else:
            redis_ok = True
    except Exception:
        redis_ok = False

    checks = {
        "database": "ok" if db_ok else "failed",
        "redis": "ok" if redis_ok else "failed",
    }

    if db_ok and redis_ok:
        status = "ok"
    elif db_ok or redis_ok:
        status = "degraded"
    else:
        status = "error"

    return {
        "status": status,
        "service": "Aiva AI Bot",
        "version": "1.0.0",
        "checks": checks,
    }


@app.post("/webhook")
async def webhook_handler(request: Request) -> dict:
    """Telegram webhook handler."""
    if settings.TELEGRAM_WEBHOOK_SECRET:
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    update = Update.model_validate(data, context={"bot": request.app.state.bot})
    await request.app.state.dp.feed_update(request.app.state.bot, update)
    return {"ok": True}


app.include_router(api_v1_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
