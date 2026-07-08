import unittest
from unittest import mock
import json
import os
from ingest_schedule import merge_schedules, process_image

class TestIngestSchedule(unittest.TestCase):
    def test_merge_schedules_no_overwrite(self):
        existing = {
            "2026-07-09": {
                "new_line": [{"start_time": "09:00", "end_time": "10:00"}]
            }
        }
        new_data = {
            "2026-07-09": {
                "old_line": [{"start_time": "05:00", "end_time": "06:00"}]
            },
            "2026-07-10": {
                "new_line": [{"start_time": "08:00", "end_time": "09:00"}]
            }
        }
        merged = merge_schedules(existing, new_data, overwrite=False)
        self.assertEqual(len(merged), 2)
        self.assertIn("new_line", merged["2026-07-09"])
        self.assertIn("old_line", merged["2026-07-09"])
        
    def test_merge_schedules_overwrite(self):
        existing = {
            "2026-07-09": {
                "new_line": [{"start_time": "09:00", "end_time": "10:00"}]
            }
        }
        new_data = {
            "2026-07-09": {
                "old_line": [{"start_time": "05:00", "end_time": "06:00"}]
            }
        }
        merged = merge_schedules(existing, new_data, overwrite=True)
        self.assertEqual(len(merged), 1)
        self.assertIn("old_line", merged["2026-07-09"])
        self.assertNotIn("new_line", merged["2026-07-09"])
        
    def test_merge_schedules_sorts_slots(self):
        existing = {}
        new_data = {
            "2026-07-09": {
                "old_line": [
                    {"start_time": "20:00", "end_time": "21:00"},
                    {"start_time": "05:00", "end_time": "06:00"}
                ]
            }
        }
        merged = merge_schedules(existing, new_data)
        self.assertEqual(merged["2026-07-09"]["old_line"][0]["start_time"], "05:00")
        self.assertEqual(merged["2026-07-09"]["old_line"][1]["start_time"], "20:00")
