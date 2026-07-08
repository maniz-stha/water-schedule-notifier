import unittest
from unittest import mock
import os
from extractor import GeminiExtractor, ExtractedScheduleSchema, ScheduleEntrySchema

class TestGeminiExtractor(unittest.TestCase):
    @mock.patch("extractor.genai.Client")
    @mock.patch("extractor.Image.open")
    @mock.patch("extractor.os.path.exists")
    def test_extract_schedule_success(self, mock_exists, mock_image_open, mock_genai_client):
        mock_exists.return_value = True
        
        # Setup mocked Gemini Client response
        mock_client_instance = mock.Mock()
        mock_genai_client.return_value = mock_client_instance
        
        expected_parsed = ExtractedScheduleSchema(
            bs_year=2081,
            bs_month=4,
            entries=[
                ScheduleEntrySchema(bs_day=1, location="पुरानाे लाइन", start_time="04:00", end_time="05:00")
            ]
        )
        
        mock_response = mock.Mock()
        mock_response.parsed = expected_parsed
        mock_client_instance.models.generate_content.return_value = mock_response
        
        extractor = GeminiExtractor(api_key="test-key")
        result = extractor.extract_schedule("dummy_path.png")
        
        self.assertEqual(result.bs_year, 2081)
        self.assertEqual(result.bs_month, 4)
        self.assertEqual(len(result.entries), 1)
        self.assertEqual(result.entries[0].bs_day, 1)
        self.assertEqual(result.entries[0].location, "पुरानाे लाइन")
