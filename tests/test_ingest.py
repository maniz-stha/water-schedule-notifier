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
                "old_line": [{"start_time": "12:00", "end_time": "13:00"}]
            }
        }
        new_data = {
            "2026-07-09": {
                "old_line": [{"start_time": "05:00", "end_time": "06:00"}]
            }
        }
        merged = merge_schedules(existing, new_data, overwrite=True)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged["2026-07-09"]["old_line"], [{"start_time": "05:00", "end_time": "06:00"}])

    def test_merge_schedules_sorting(self):
        existing = {
            "2026-07-15": {
                "old_line": []
            }
        }
        new_data = {
            "2026-07-05": {
                "old_line": []
            }
        }
        merged = merge_schedules(existing, new_data)
        keys = list(merged.keys())
        self.assertEqual(keys, ["2026-07-05", "2026-07-15"])
        
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

    @mock.patch("ingest_schedule.GeminiExtractor")
    @mock.patch("ingest_schedule.load_ai_config")
    @mock.patch("ingest_schedule.os.path.exists")
    @mock.patch("ingest_schedule.open", new_callable=mock.mock_open, read_data="{}")
    def test_process_image_fallback_target_location(self, mock_file, mock_exists, mock_load_config, mock_extractor_class):
        mock_exists.return_value = True
        mock_load_config.return_value = {
            "GEMINI_API_KEY": "dummy",
            "GEMINI_MODEL": "gemini-2.0-flash",
            "TARGET_LOCATION": "config-location"
        }
        
        mock_extractor_instance = mock.Mock()
        mock_extractor_class.return_value = mock_extractor_instance
        
        from extractor import ExtractedScheduleSchema
        mock_extractor_instance.extract_schedule.return_value = ExtractedScheduleSchema(
            bs_year=2081,
            bs_month=4,
            entries=[]
        )
        
        process_image("dummy_img.png", overwrite=False, env_file=".env", schedule_json_path="dummy_db.json", target_location=None)
        
        mock_extractor_instance.extract_schedule.assert_called_once_with("dummy_img.png", target_location="config-location")

    def test_clean_and_sort_json_file_handles_duplicates(self):
        temp_file = "test_duplicate_schedule.json"
        raw_json = """{
            "2026-07-15": {
                "old_line": [{"start_time": "05:00", "end_time": "06:00"}]
            },
            "2026-07-10": {
                "new_line": [{"start_time": "09:00", "end_time": "21:00"}]
            },
            "2026-07-15": {
                "new_line": [{"start_time": "09:00", "end_time": "21:00"}]
            }
        }"""
        
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(raw_json)
            
        try:
            from ingest_schedule import clean_and_sort_json_file
            clean_and_sort_json_file(temp_file)
            
            with open(temp_file, "r", encoding="utf-8") as f:
                cleaned = json.load(f)
                
            keys = list(cleaned.keys())
            self.assertEqual(keys, ["2026-07-10", "2026-07-15"])
            self.assertIn("old_line", cleaned["2026-07-15"])
            self.assertIn("new_line", cleaned["2026-07-15"])
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    @mock.patch("ingest_schedule.GeminiExtractor")
    @mock.patch("ingest_schedule.load_ai_config")
    @mock.patch("ingest_schedule.os.path.exists")
    @mock.patch("ingest_schedule.open", new_callable=mock.mock_open, read_data="{}")
    def test_process_image_fallback_bs_year(self, mock_file, mock_exists, mock_load_config, mock_extractor_class):
        mock_exists.return_value = True
        mock_load_config.return_value = {
            "GEMINI_API_KEY": "dummy",
            "GEMINI_MODEL": "gemini-2.0-flash"
        }
        
        mock_extractor_instance = mock.Mock()
        mock_extractor_class.return_value = mock_extractor_instance
        
        from extractor import ExtractedScheduleSchema, ScheduleEntrySchema
        mock_extractor_instance.extract_schedule.return_value = ExtractedScheduleSchema(
            bs_year=0,
            bs_month=3,
            entries=[
                ScheduleEntrySchema(bs_day=1, location="old_line", start_time="05:00", end_time="06:00")
            ]
        )
        
        import nepali_datetime
        current_year = nepali_datetime.date.today().year
        
        process_image("dummy_img.png", overwrite=False, env_file=".env", schedule_json_path="dummy_db.json")
        
        from date_converter import convert_bs_to_ad
        expected_ad = convert_bs_to_ad(current_year, 3, 1)
        
        # Verify it writes to dummy_db.json
        mock_file.assert_any_call("dummy_db.json", "w", encoding="utf-8")



