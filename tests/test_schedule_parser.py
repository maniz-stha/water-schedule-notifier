import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from schedule_parser import find_slots_starting_in_hour

class TestScheduleParser(unittest.TestCase):
    def setUp(self):
        self.sample_schedule = {
            "2026-07-05": {
                "old_line": [
                    {"start_time": "04:00", "end_time": "05:00"},
                    {"start_time": "20:00", "end_time": "21:00"}
                ],
                "new_line": [
                    {"start_time": "09:00", "end_time": "21:00"}
                ]
            }
        }
        self.tz = ZoneInfo("Asia/Kathmandu")

    def test_matching_slot_exact_start(self):
        # Run check at 2026-07-05 04:00:00
        check_dt = datetime(2026, 7, 5, 4, 0, 0, tzinfo=self.tz)
        slots = find_slots_starting_in_hour(self.sample_schedule, check_dt)
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]["pipeline"], "Old")
        self.assertEqual(slots[0]["start_time"], "04:00")
        self.assertEqual(slots[0]["delay_seconds"], 0)

    def test_matching_slot_future_within_hour(self):
        # Run check at 2026-07-05 08:15:00, slot starts at 09:00 (45 mins / 2700s delay)
        check_dt = datetime(2026, 7, 5, 8, 15, 0, tzinfo=self.tz)
        slots = find_slots_starting_in_hour(self.sample_schedule, check_dt)
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]["pipeline"], "New")
        self.assertEqual(slots[0]["start_time"], "09:00")
        self.assertEqual(slots[0]["delay_seconds"], 2700)

    def test_no_matching_slots(self):
        # Run check at 2026-07-05 10:00:00 (next slot is 20:00, which is > 1 hour away)
        check_dt = datetime(2026, 7, 5, 10, 0, 0, tzinfo=self.tz)
        slots = find_slots_starting_in_hour(self.sample_schedule, check_dt)
        self.assertEqual(len(slots), 0)
