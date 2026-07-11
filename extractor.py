import os
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
from PIL import Image
from google import genai
from google.genai import types

class ScheduleEntrySchema(BaseModel):
    bs_day: int = Field(description="The day of the month in B.S. calendar (1 to 32)")
    location: str = Field(description="The pipeline identifier. Must be either 'old_line' (for old pipeline / पुरानो पाइपलाइन) or 'new_line' (for new pipeline / नयाँ पाइपलाइन). Determine this from the image context (e.g. table title or header).")
    start_time: str = Field(description="The start time in 24-hour HH:MM format (e.g., '04:00', '20:15')")
    end_time: str = Field(description="The end time in 24-hour HH:MM format (e.g., '05:00', '21:15')")

class ExtractedScheduleSchema(BaseModel):
    bs_year: int = Field(description="The B.S. year (e.g. 2083). If the year is not explicitly mentioned anywhere in the image, return 0.")
    bs_month: int = Field(description="The B.S. month (as a number 1 to 12)")
    entries: List[ScheduleEntrySchema] = Field(description="List of schedule entries")

class BaseExtractor(ABC):
    @abstractmethod
    def extract_schedule(self, image_path: str, target_location: Optional[str] = None) -> ExtractedScheduleSchema:
        """Extract schedule from an image containing a table."""
        pass

class GeminiExtractor(BaseExtractor):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()
        self.model = model

    def extract_schedule(self, image_path: str, target_location: Optional[str] = None) -> ExtractedScheduleSchema:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found at: {image_path}")
            
        try:
            image = Image.open(image_path)
        except Exception as e:
            raise ValueError(f"Failed to open image file: {e}")
            
        prompt = (
            "Analyze this water schedule image. The schedule is for a single month in the Bikram Sambat (B.S.) calendar, "
            "written in Nepali language (Devanagari script). "
            "Please extract the B.S. year, the B.S. month (as a number 1 to 12), and the list of schedule entries. "
            "For each entry, determine the B.S. day of the month, the start time, and the end time. "
            "Crucially, identify whether the entry belongs to the old pipeline ('old_line') or the new pipeline ('new_line') "
            "by looking at the table header, title, or context (e.g., 'पुरानो पाइपलाइन' or 'नयाँ पाइपलाइन'), and set this as the 'location'. "
            "Ensure times are in 24-hour HH:MM format. "
            "If the calendar year is not explicitly written in the image, return 0 for bs_year."
        )

        
        if target_location:
            prompt += (
                f"\n\nCRITICAL: Only extract schedule entries from the table rows whose list of water distribution areas "
                f"('पानी वितरण हुने स्थान') contains the target location '{target_location}' (match transliterated English or native Devanagari). "
                f"Ignore all rows that do not cover this location."
            )
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedScheduleSchema,
            ),
        )
        return response.parsed
