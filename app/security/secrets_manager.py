
"""
Secure secrets management system for Mirai Agent
"""

import logging
import os
import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from pathlib import Path

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Secure secrets management system using encryption
    """

    def __init__(self, key_file: Optional[str] = None):
        """
        Initialize secrets manager

        Args:
            key_file: Optional path to encryption key file
        """
        self.key_file = key_file or os.path.join(os.path.dirname(__file__), "secret.key")
        self._cipher_suite = None
        self._load_or_create_key()

    def _load_or_create_key(self):
        """Load existing encryption key or create a new one"""
        try:
            if os.path.exists(self.key_file):
                # Load existing key
                with open(self.key_file, "rb") as f:
                    key = f.read()
                self._cipher_suite = Fernet(key)
                logger.info("Loaded existing encryption key")
            else:
                # Create new key
                key = Fernet.generate_key()
                self._cipher_suite = Fernet(key)

                # Save key to file
                os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
                with open(self.key_file, "wb") as f:
                    f.write(key)

                # Set restrictive permissions
                os.chmod(self.key_file, 0o600)
                logger.info("Created new encryption key")
        except Exception as e:
            logger.error(f"Error initializing encryption key: {str(e)}")
            raise

    def encrypt(self, data: str) -> bytes:
        """
        Encrypt string data

        Args:
            data: String data to encrypt

        Returns:
            Encrypted data as bytes
        """
        if not self._cipher_suite:
            raise ValueError("Cipher suite not initialized")
        return self._cipher_suite.encrypt(data.encode())

    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypt bytes data

        Args:
            encrypted_data: Encrypted data as bytes

        Returns:
            Decrypted string data
        """
        if not self._cipher_suite:
            raise ValueError("Cipher suite not initialized")
        return self._cipher_suite.decrypt(encrypted_data).decode()

    def encrypt_dict(self, data: Dict[str, Any]) -> bytes:
        """
        Encrypt dictionary data

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted data as bytes
        """
        json_data = json.dumps(data, separators=(",", ":"), sort_keys=True)
        return self.encrypt(json_data)

    def decrypt_dict(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Decrypt bytes data to dictionary

        Args:
            encrypted_data: Encrypted data as bytes

        Returns:
            Decrypted dictionary
        """
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)

    def save_secrets(self, secrets: Dict[str, Any], file_path: str) -> bool:
        """
        Save encrypted secrets to file

        Args:
            secrets: Dictionary with secrets
            file_path: Path to save encrypted secrets

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Encrypt secrets
            encrypted_data = self.encrypt_dict(secrets)

            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save encrypted data
            with open(file_path, "wb") as f:
                f.write(encrypted_data)

            # Set restrictive permissions
            os.chmod(file_path, 0o600)

            logger.info(f"Successfully saved encrypted secrets to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving encrypted secrets: {str(e)}")
            return False

    def load_secrets(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load encrypted secrets from file

        Args:
            file_path: Path to encrypted secrets file

        Returns:
            Dictionary with secrets if loaded successfully, None otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Secrets file not found: {file_path}")
                return None

            with open(file_path, "rb") as f:
                encrypted_data = f.read()

            secrets = self.decrypt_dict(encrypted_data)
            logger.info(f"Successfully loaded secrets from {file_path}")
            return secrets
        except Exception as e:
            logger.error(f"Error loading encrypted secrets: {str(e)}")
            return None

    def get_secret(self, key: str, file_path: str) -> Optional[str]:
        """
        Get a specific secret from file

        Args:
            key: Secret key to retrieve
            file_path: Path to encrypted secrets file

        Returns:
            Secret value if found, None otherwise
        """
        secrets = self.load_secrets(file_path)
        return secrets.get(key) if secrets else None

    def set_secret(self, key: str, value: str, file_path: str) -> bool:
        """
        Set a specific secret in file

        Args:
            key: Secret key to set
            value: Secret value
            file_path: Path to encrypted secrets file

        Returns:
            True if set successfully, False otherwise
        """
        secrets = self.load_secrets(file_path) or {}
        secrets[key] = value
        return self.save_secrets(secrets, file_path)

    def delete_secret(self, key: str, file_path: str) -> bool:
        """
        Delete a specific secret from file

        Args:
            key: Secret key to delete
            file_path: Path to encrypted secrets file

        Returns:
            True if deleted successfully, False otherwise
        """
        secrets = self.load_secrets(file_path)
        if not secrets:
            return False

        if key in secrets:
            del secrets[key]
            return self.save_secrets(secrets, file_path)
        return False

    def update_environment_variables(self, file_path: str) -> bool:
        """
        Load secrets from file and update environment variables

        Args:
            file_path: Path to encrypted secrets file

        Returns:
            True if updated successfully, False otherwise
        """
        secrets = self.load_secrets(file_path)
        if not secrets:
            return False

        updated = 0
        for key, value in secrets.items():
            os.environ[key] = str(value)
            updated += 1

        logger.info(f"Updated {updated} environment variables from secrets file")
        return True
