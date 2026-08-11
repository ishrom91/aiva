#!/usr/bin/env python3
"""
Smoke-test: эмулирует сценарий мастера без Telegram polling.

1. /start — создаёт мастера
2. /add_service — добавляет «Маникюр 2500₽»
3. /book — проходит FSM и создаёт первую запись
4. Создаёт ещё 49 записей (итого 50)
5. Проверяет, что сработал upsell-триггер limit (≥90% лимита)

Запуск из корня проекта:
    python scripts/smoke_test.py
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SMOKE_DB_FILE = ROOT / "smoke_test.db"
SMOKE_DB_SYNC = f"sqlite:///{SMOKE_DB_FILE.as_posix()}"
SMOKE_DB_ASYNC = f"sqlite+aiosqlite:///{SMOKE_DB_FILE.as_posix()}"
MASTER_TELEGRAM_ID = 9_998_887_77


class TrackedState:
    """In-memory FSM state for handler calls without Telegram."""

    def __init__(self) -> None:
        self._data: dict = {}
        self._state = AsyncMock(spec=FSMContext)
        self._state.set_state = AsyncMock()
        self._state.clear = AsyncMock()
        self._state.update_data = self.update_data
        self._state.get_data = self.get_data

    @property
    def ctx(self) -> FSMContext:
        return self._state

    async def update_data(self, **kwargs: object) -> None:
        self._data.update(kwargs)

    async def get_data(self) -> dict:
        return self._data.copy()


def _user() -> User:
    return User(
        id=MASTER_TELEGRAM_ID,
        is_bot=False,
        first_name="Smoke",
        last_name="Master",
        username="smoke_master",
    )


def _message(text: str = "") -> Message:
    msg = AsyncMock(spec=Message)
    msg.from_user = _user()
    msg.text = text
    msg.answer = AsyncMock()
    msg.edit_text = AsyncMock()
    return msg


def _callback(data: str) -> CallbackQuery:
    cb = AsyncMock(spec=CallbackQuery)
    cb.from_user = _user()
    cb.data = data
    cb.answer = AsyncMock()
    cb.message = AsyncMock()
    cb.message.edit_text = AsyncMock()
    return cb


def _migrate_db() -> None:
    if SMOKE_DB_FILE.exists():
        SMOKE_DB_FILE.unlink()
    env = os.environ.copy()
    env["DATABASE_URL"] = SMOKE_DB_SYNC
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=ROOT,
        check=True,
        env=env,
    )


def _ok(step: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"  [OK] {step}{suffix}")


def _fail(step: str, detail: str) -> None:
    print(f"  [FAIL] {step}: {detail}", file=sys.stderr)


async def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    from src.billing.upsell_triggers import check_upsell_triggers
    from src.database import close_db, get_session, init_db
    from src.handlers.admin import (
        add_service_command,
        add_service_duration,
        add_service_name,
        add_service_price,
    )
    from src.handlers.booking import (
        command_book_handler,
        confirm_booking,
        process_date_selection,
        process_service_selection,
        process_time_selection,
    )
    from src.handlers.start import start_command
    from src.models.booking import Booking
    from src.models.master import Master
    from src.models.service import Service
    from src.models.subscription import Subscription
    from src.services.booking_service import BookingService
    from src.services.master_service import get_master_by_telegram_id
    from src.services.subscription_service import SubscriptionService

    print("Aiva smoke test (bez Telegram polling)\n")

    _migrate_db()
    await init_db(SMOKE_DB_ASYNC)

    state = TrackedState()
    noop_log = patch("src.utils.event_log.log_event")
    noop_log.start()

    try:
        # --- 1. /start ---
        print("1. /start")
        await start_command(_message("/start"), state.ctx)

        async with get_session() as session:
            master = await get_master_by_telegram_id(session, MASTER_TELEGRAM_ID)
            sub_count = await session.scalar(select(func.count()).select_from(Subscription))
        if not master:
            _fail("/start", "Master не создан")
            return 1
        if not sub_count:
            _fail("/start", "Subscription не создан")
            return 1
        _ok("Master создан", f"id={master.id[:8]}…, trial subscription OK")

        # --- 2. /add_service ---
        print("2. /add_service → «Маникюр 2500₽»")
        await add_service_command(_message("/add_service"), state.ctx)
        await add_service_name(_message("Маникюр"), state.ctx)
        await add_service_duration(_message("60"), state.ctx)
        await add_service_price(_message("2500"), state.ctx)

        async with get_session() as session:
            service = await session.scalar(
                select(Service).where(Service.master_id == master.id)
            )
        if not service or service.name != "Маникюр" or service.price != 2500:
            _fail("/add_service", f"ожидали Маникюр 2500₽, получили {service}")
            return 1
        _ok("Услуга добавлена", f"{service.name}, {service.duration_minutes} мин, {service.price}₽")

        # --- 3. /book FSM ---
        print("3. /book — FSM цикл")
        await command_book_handler(_message("/book"), state.ctx)
        await process_service_selection(_callback(f"service_{service.id}"), state.ctx)

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        await process_date_selection(_callback(f"date_{tomorrow}"), state.ctx)

        data = await state.get_data()
        booking_dt_str = data.get("selected_datetime")
        if not booking_dt_str:
            # pick first available slot from state after date step
            time_cb = _callback("time_09:00")
            await process_time_selection(time_cb, state.ctx)
            booking_dt_str = (await state.get_data()).get("selected_datetime")

        if not booking_dt_str:
            _fail("/book", "не удалось выбрать время")
            return 1

        await confirm_booking(_callback(f"confirm_{booking_dt_str}"), state.ctx)

        async with get_session() as session:
            after_fsm = await session.scalar(
                select(func.count()).select_from(Booking).where(Booking.master_id == master.id)
            )
        if not after_fsm:
            _fail("/book", "запись через FSM не создана")
            return 1
        _ok("FSM завершён", f"1 запись на {booking_dt_str}")

        # --- 4. Ещё 49 записей (итого 50) ---
        print("4. Создание 50 записей (49 bulk + 1 из FSM)")
        async with get_session() as session:
            master = await get_master_by_telegram_id(session, MASTER_TELEGRAM_ID)
            assert master is not None
            from src.handlers.helpers import get_or_create_client

            client, _ = await get_or_create_client(
                session, MASTER_TELEGRAM_ID, master.id, "Smoke Client"
            )
            booking_service = BookingService(session)
            base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(
                days=2
            )
            created = 0
            for i in range(200):
                when = base + timedelta(days=i // 9, minutes=30 * (i % 9))
                try:
                    await booking_service.create_booking(
                        master_id=master.id,
                        client_id=client.id,
                        service_id=service.id,
                        booking_datetime=when,
                    )
                    created += 1
                except Exception:
                    continue
                if created >= 49:
                    break

            total = await session.scalar(
                select(func.count()).select_from(Booking).where(Booking.master_id == master.id)
            )

        if total != 50:
            _fail("bookings", f"ожидали 50 записей, получили {total}")
            return 1
        _ok("50 записей создано")

        # --- 5. Upsell trigger ---
        print("5. Upsell-триггер при ≥90% лимита")
        async with get_session() as session:
            master = await session.get(Master, master.id)
            assert master is not None
            master.settings = {
                "last_lost_revenue_demo": datetime.now().isoformat(),
                "last_social_proof": datetime.now().isoformat(),
            }
            await session.commit()

            sub_service = SubscriptionService()
            usage = await sub_service.current_month_usage(session, master.id)
            trigger = await check_upsell_triggers(session, master.id)

        if usage < 45:
            _fail("usage", f"ожидали ≥45 записей в месяце, получили {usage}")
            return 1

        if not trigger or not trigger.get("should_upsell"):
            _fail("upsell", f"триггер не сработал: {trigger}")
            return 1
        if trigger.get("trigger_type") != "limit":
            _fail("upsell", f"ожидали trigger_type=limit, получили {trigger.get('trigger_type')}")
            return 1

        _ok(
            "Upsell limit",
            f"usage={usage}/50, target={trigger.get('target_tariff')}",
        )
        print("\nSmoke test PASSED — all 5 steps OK")
        return 0

    finally:
        noop_log.stop()
        await close_db()
        if SMOKE_DB_FILE.exists():
            SMOKE_DB_FILE.unlink()


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except subprocess.CalledProcessError as exc:
        print(f"FAIL: DB migration failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
