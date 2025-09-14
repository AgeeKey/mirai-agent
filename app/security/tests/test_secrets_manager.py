
"""
Tests for secrets manager module
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from secrets_manager import SecretsManager


class TestSecretsManager(unittest.TestCase):
    """Test cases for SecretsManager"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.key_file = os.path.join(self.test_dir, "test.key")
        self.secrets_file = os.path.join(self.test_dir, "secrets.enc")

        # Ensure we're using test files
        with patch.object(SecretsManager, '_load_or_create_key'):
            self.secrets_manager = SecretsManager(key_file=self.key_file)

    def tearDown(self):
        """Clean up test environment"""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_key_creation(self):
        """Test encryption key creation"""
        self.assertTrue(os.path.exists(self.key_file))

        # Check file permissions
        stat_info = os.stat(self.key_file)
        self.assertEqual(stat_info.st_mode & 0o777, 0o600)

    def test_encryption_decryption(self):
        """Test basic encryption and decryption"""
        test_data = "This is a secret message"

        # Encrypt
        encrypted = self.secrets_manager.encrypt(test_data)
        self.assertIsInstance(encrypted, bytes)

        # Decrypt
        decrypted = self.secrets_manager.decrypt(encrypted)
        self.assertEqual(decrypted, test_data)

    def test_dict_encryption_decryption(self):
        """Test dictionary encryption and decryption"""
        test_dict = {
            "api_key": "test123",
            "secret_key": "secret456",
            "other_data": {
                "nested": "value"
            }
        }

        # Encrypt
        encrypted = self.secrets_manager.encrypt_dict(test_dict)
        self.assertIsInstance(encrypted, bytes)

        # Decrypt
        decrypted = self.secrets_manager.decrypt_dict(encrypted)
        self.assertEqual(decrypted, test_dict)

    def test_save_load_secrets(self):
        """Test saving and loading secrets"""
        test_secrets = {
            "BINANCE_API_KEY": "test123",
            "BINANCE_SECRET_KEY": "secret456",
            "TELEGRAM_BOT_TOKEN": "bot123"
        }

        # Save secrets
        result = self.secrets_manager.save_secrets(test_secrets, self.secrets_file)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.secrets_file))

        # Check file permissions
        stat_info = os.stat(self.secrets_file)
        self.assertEqual(stat_info.st_mode & 0o777, 0o600)

        # Load secrets
        loaded_secrets = self.secrets_manager.load_secrets(self.secrets_file)
        self.assertEqual(loaded_secrets, test_secrets)

    def test_get_set_secret(self):
        """Test getting and setting individual secrets"""
        # Set a secret
        result = self.secrets_manager.set_secret("API_KEY", "test123", self.secrets_file)
        self.assertTrue(result)

        # Get the secret
        secret = self.secrets_manager.get_secret("API_KEY", self.secrets_file)
        self.assertEqual(secret, "test123")

        # Get non-existent secret
        secret = self.secrets_manager.get_secret("NON_EXISTENT", self.secrets_file)
        self.assertIsNone(secret)

    def test_delete_secret(self):
        """Test deleting a secret"""
        # Set multiple secrets
        self.secrets_manager.set_secret("API_KEY", "test123", self.secrets_file)
        self.secrets_manager.set_secret("SECRET_KEY", "secret456", self.secrets_file)

        # Delete one secret
        result = self.secrets_manager.delete_secret("API_KEY", self.secrets_file)
        self.assertTrue(result)

        # Verify deletion
        secrets = self.secrets_manager.load_secrets(self.secrets_file)
        self.assertNotIn("API_KEY", secrets)
        self.assertIn("SECRET_KEY", secrets)

    def test_update_environment_variables(self):
        """Test updating environment variables"""
        test_secrets = {
            "API_KEY": "test123",
            "SECRET_KEY": "secret456"
        }

        # Save secrets
        self.secrets_manager.save_secrets(test_secrets, self.secrets_file)

        # Update environment variables
        result = self.secrets_manager.update_environment_variables(self.secrets_file)
        self.assertTrue(result)

        # Check environment variables
        self.assertEqual(os.environ.get("API_KEY"), "test123")
        self.assertEqual(os.environ.get("SECRET_KEY"), "secret456")

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file"""
        secrets = self.secrets_manager.load_secrets("/nonexistent/file.enc")
        self.assertIsNone(secrets)

    def test_invalid_encrypted_data(self):
        """Test handling invalid encrypted data"""
        # Create a file with invalid data
        with open(self.secrets_file, "wb") as f:
            f.write(b"invalid encrypted data")

        # Try to load
        secrets = self.secrets_manager.load_secrets(self.secrets_file)
        self.assertIsNone(secrets)


if __name__ == "__main__":
    unittest.main()
