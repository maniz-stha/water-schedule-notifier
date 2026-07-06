import unittest
from unittest import mock
from datetime import datetime
from zoneinfo import ZoneInfo
import notifier

class TestNotifierRunner(unittest.TestCase):
    @mock.patch("notifier.time.sleep")
    @mock.patch("notifier.send_telegram_message")
    def test_runner_execution(self, mock_send, mock_sleep):
        sample_schedule = {
            "2026-07-06": {
                "old_line": [{"start_time": "22:15", "end_time": "23:00"}]
            }
        }
        mock_send.return_value = True
        
        # Current time is 22:00:00 (15 min delay / 900 seconds)
        tz = ZoneInfo("Asia/Kathmandu")
        now = datetime(2026, 7, 6, 22, 0, 0, tzinfo=tz)
        
        notifier.run_notifications(
            schedule_data=sample_schedule,
            current_time=now,
            bot_token="token",
            chat_id="chat"
        )
        
        # Verify it slept 900 seconds (15 minutes) and then sent the correct alert
        mock_sleep.assert_called_once_with(900.0)
        expected_msg = (
            "**Water Alert - 2026-07-06**\n"
            "Pipeline: Old\n"
            "Start: 22:15\n"
            "End: 23:00"
        )
        mock_send.assert_called_once_with("token", "chat", expected_msg)
