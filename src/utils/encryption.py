from cryptography.fernet import Fernet
from typing import Union
import base64
import os


class EncryptionManager:
    """Manager for encrypting and decrypting sensitive data"""
    
    def __init__(self, encryption_key: Union[str, bytes]):
        """
        Initialize the encryption manager with the provided key.
        
        Args:
            encryption_key: Either a base64-encoded string key or raw bytes
        """
        if isinstance(encryption_key, str):
            # Ensure the key is properly formatted for Fernet
            if len(encryption_key) != 44 or not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in encryption_key):
                # If it's not a valid base64 key, we assume it's a raw password that needs to be converted
                encryption_key = self._generate_key_from_password(encryption_key)
            else:
                # It's already a valid base64 key
                pass
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.cipher_suite = Fernet(encryption_key)
    
    def _generate_key_from_password(self, password: str) -> bytes:
        """
        Generate a valid Fernet key from a password.
        This is a simple approach - in production, use proper key derivation.
        """
        # Pad or truncate the password to 32 bytes and encode in base64
        key_bytes = password.ljust(32)[:32].encode('utf-8')
        encoded_key = base64.urlsafe_b64encode(key_bytes)
        return encoded_key
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Encrypt the provided data.
        
        Args:
            data: Data to encrypt (string or bytes)
            
        Returns:
            str: Base64-encoded encrypted data
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self.cipher_suite.encrypt(data)
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        """
        Decrypt the provided data.
        
        Args:
            encrypted_data: Encrypted data (base64 string or bytes)
            
        Returns:
            str: Decrypted data as string
        """
        if isinstance(encrypted_data, str):
            encrypted_data = base64.b64decode(encrypted_data.encode('utf-8'))
        
        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')


def get_encryption_manager(encryption_key: str) -> EncryptionManager:
    """
    Create an encryption manager instance.
    
    Args:
        encryption_key: The encryption key from settings
        
    Returns:
        EncryptionManager: Instance of the encryption manager
    """
    return EncryptionManager(encryption_key)


# Convenience functions
def encrypt_phone(phone: str, encryption_key: str) -> str:
    """
    Encrypt a phone number.
    
    Args:
        phone: Phone number to encrypt
        encryption_key: The encryption key
        
    Returns:
        str: Encrypted phone number
    """
    manager = get_encryption_manager(encryption_key)
    return manager.encrypt(phone)


def decrypt_phone(encrypted_phone: str, encryption_key: str) -> str:
    """
    Decrypt a phone number.
    
    Args:
        encrypted_phone: Encrypted phone number
        encryption_key: The encryption key
        
    Returns:
        str: Decrypted phone number
    """
    manager = get_encryption_manager(encryption_key)
    return manager.decrypt(encrypted_phone)