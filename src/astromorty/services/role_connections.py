"""
Secure Token Storage Service.

This module provides encryption and decryption services for OAuth tokens
stored in the database, ensuring sensitive data is protected at rest.
"""

from __future__ import annotations

import base64
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger


class SecureTokenStorage:
    """
    Secure storage service for OAuth tokens.

    Uses Fernet symmetric encryption to protect OAuth tokens
    stored in the database, with key derivation for additional security.
    """

    def __init__(self, encryption_key: str | None = None) -> None:
        """
        Initialize the secure token storage.

        Parameters
        ----------
        encryption_key : str | None
            Encryption key for token storage. If None, uses environment key.
        """
        self._fernet: Fernet | None = None
        self._initialize_encryption(encryption_key)

    def _initialize_encryption(self, encryption_key: str | None = None) -> None:
        """
        Initialize the encryption cipher.

        Parameters
        ----------
        encryption_key : str | None
            Encryption key for token storage
        """
        try:
            if encryption_key:
                # Use provided key directly (must be URL-safe base64 encoded)
                key = base64.urlsafe_b64decode(encryption_key.encode())
            else:
                # Derive key from environment or use a default for development
                import os
                from astromorty.shared.config import CONFIG

                env_key = os.getenv("ROLE_CONNECTIONS_SECRET_KEY")
                if env_key:
                    # Derive key from environment key
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=b"astromorty_role_connections_salt",
                        iterations=100000,
                    )
                    key = kdf.derive(env_key.encode())
                else:
                    # Development fallback - use a fixed key
                    logger.warning(
                        "Using development encryption key - not secure for production"
                    )
                    key = b"astromorty_dev_key_32_bytes_long"

            # Ensure key is 32 bytes for Fernet
            if len(key) < 32:
                key = key.ljust(32, b"\0")
            elif len(key) > 32:
                key = key[:32]

            self._fernet = Fernet(base64.urlsafe_b64encode(key))
            logger.debug("Secure token storage initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize secure token storage: {e}")
            raise

    def encrypt_token(self, token: str) -> str:
        """
        Encrypt a token for secure storage.

        Parameters
        ----------
        token : str
            Plain text token to encrypt

        Returns
        -------
        str
            Encrypted token (base64 encoded)

        Raises
        ------
        RuntimeError
            If encryption is not initialized
        """
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")

        try:
            encrypted = self._fernet.encrypt(token.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt token: {e}")
            raise

    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt a stored token.

        Parameters
        ----------
        encrypted_token : str
            Encrypted token (base64 encoded)

        Returns
        -------
        str
            Decrypted plain text token

        Raises
        ------
        RuntimeError
            If encryption is not initialized
        """
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")

        try:
            # Decode base64 and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            raise

    def is_available(self) -> bool:
        """
        Check if encryption is available.

        Returns
        -------
        bool
            True if encryption is initialized and available
        """
        return self._fernet is not None


# Global instance for use throughout the application
_token_storage: SecureTokenStorage | None = None


def get_token_storage() -> SecureTokenStorage:
    """
    Get the global token storage instance.

    Returns
    -------
    SecureTokenStorage
        Global token storage instance

    Raises
    ------
    RuntimeError
        If token storage cannot be initialized
    """
    global _token_storage

    if _token_storage is None:
        _token_storage = SecureTokenStorage()
        if not _token_storage.is_available():
            raise RuntimeError("Failed to initialize secure token storage")

    return _token_storage


# Export the main class and convenience function
__all__ = ["SecureTokenStorage", "get_token_storage"]
