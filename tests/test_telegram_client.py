import unittest
from unittest import mock
from urllib.error import URLError
from telegram_client import send_telegram_message

class TestTelegramClient(unittest.TestCase):
    @mock.patch("urllib.request.urlopen")
    def test_send_message_success(self, mock_urlopen):
        # Mock response object with read() method
        mock_response = mock.Mock()
        mock_response.read.return_value = b'{"ok": true}'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        success = send_telegram_message("token", "chat", "test alert")
        self.assertTrue(success)
        mock_urlopen.assert_called_once()

    @mock.patch("urllib.request.urlopen")
    def test_send_message_failure_retries(self, mock_urlopen):
        # Simulate URLError for 3 consecutive attempts
        mock_urlopen.side_effect = URLError("Network timeout")
        # Mock time.sleep to make the test run instantly
        with mock.patch("telegram_client.time.sleep") as mock_sleep:
            success = send_telegram_message("token", "chat", "test alert")
            self.assertFalse(success)
            self.assertEqual(mock_urlopen.call_count, 3)
            self.assertEqual(mock_sleep.call_count, 2)
