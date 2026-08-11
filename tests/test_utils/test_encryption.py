"""Tests for client PII encryption (152-FZ)."""

import pytest

from src.config import settings
from src.handlers.helpers import get_or_create_client
from src.utils.encryption import get_encryption_manager
from tests.conftest import make_master


@pytest.mark.asyncio
async def test_client_phone_encrypted(db_session):
    master = await make_master(db_session, telegram_id=801001)
    phone = "+79991234567"
    name = "Ivan Petrov"

    client, created = await get_or_create_client(
        db_session,
        telegram_id=801002,
        master_id=master.id,
        name=name,
        phone=phone,
    )

    assert created is True
    assert client.phone_encrypted is not None
    assert client.name_encrypted is not None
    assert client.phone_encrypted != phone
    assert client.name_encrypted != name

    manager = get_encryption_manager(settings.ENCRYPTION_KEY)
    assert manager.decrypt(client.phone_encrypted) == phone
    assert manager.decrypt(client.name_encrypted) == name
