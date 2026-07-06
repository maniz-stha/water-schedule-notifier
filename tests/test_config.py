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
