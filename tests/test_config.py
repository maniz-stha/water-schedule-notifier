import os
import unittest
from unittest import mock
from config import load_config

class TestConfig(unittest.TestCase):
    @mock.patch.dict(os.environ, {
        "TELEGRAM_BOT_TOKEN": "test-token",
        "TELEGRAM_CHAT_ID": "test-chat-id"
    })
    def test_load_config_success(self):
        config = load_config(env_file=None)
        self.assertEqual(config["TELEGRAM_BOT_TOKEN"], "test-token")
        self.assertEqual(config["TELEGRAM_CHAT_ID"], "test-chat-id")

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_config_missing_keys(self):
        with self.assertRaises(ValueError) as ctx:
            load_config(env_file=None)
        self.assertIn("Missing required environment variables", str(ctx.exception))

    def test_load_ai_config_success(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123", "GEMINI_MODEL": "gemini-2.0-flash"}):
            from config import load_ai_config
            ai_config = load_ai_config(env_file=None)
            self.assertEqual(ai_config["GEMINI_API_KEY"], "test-key-123")
            self.assertEqual(ai_config["GEMINI_MODEL"], "gemini-2.0-flash")

    def test_load_ai_config_missing_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            from config import load_ai_config
            with self.assertRaises(ValueError):
                load_ai_config(env_file=None)

