"""Encryption utilities for Aiva AI Bot (152-FZ compliant client PII)."""

import base64
import hashlib
import logging
from typing import Union

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Encrypt/decrypt sensitive client data with Fernet."""

    def __init__(self, encryption_key: Union[str, bytes]) -> None:
        key_bytes = self._normalize_key(encryption_key)
        self.cipher_suite = Fernet(key_bytes)

    @staticmethod
    def _normalize_key(encryption_key: Union[str, bytes]) -> bytes:
        """Use key as Fernet key or derive via base64(sha256(key))."""
        if isinstance(encryption_key, bytes):
            raw = encryption_key.decode("utf-8", errors="replace")
        else:
            raw = encryption_key

        try:
            candidate = raw.encode("utf-8")
            Fernet(candidate)
            return candidate
        except (ValueError, TypeError):
            digest = hashlib.sha256(raw.encode("utf-8")).digest()
            return base64.urlsafe_b64encode(digest)

    def encrypt(self, data: Union[str, bytes]) -> str:
        if isinstance(data, str):
            data = data.encode("utf-8")
        encrypted_data = self.cipher_suite.encrypt(data)
        return base64.b64encode(encrypted_data).decode("utf-8")

    def decrypt(self, encrypted_data: Union[str, bytes]) -> str | None:
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = base64.b64decode(encrypted_data.encode("utf-8"))
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode("utf-8")
        except InvalidToken:
            logger.warning("Failed to decrypt value: invalid Fernet token")
            return None


def get_encryption_manager(encryption_key: str) -> EncryptionManager:
    return EncryptionManager(encryption_key)


def encrypt(value: str, encryption_key: str | None = None) -> str:
    from ..config import settings

    key = encryption_key or settings.ENCRYPTION_KEY
    return get_encryption_manager(key).encrypt(value)


def decrypt(token: str, encryption_key: str | None = None) -> str | None:
    from ..config import settings

    key = encryption_key or settings.ENCRYPTION_KEY
    return get_encryption_manager(key).decrypt(token)


def encrypt_phone(phone: str, encryption_key: str) -> str:
    return get_encryption_manager(encryption_key).encrypt(phone)


def decrypt_phone(encrypted_phone: str, encryption_key: str) -> str | None:
    return get_encryption_manager(encryption_key).decrypt(encrypted_phone)
