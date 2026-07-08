import os
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
from PIL import Image
from google import genai
from google.genai import types

class ScheduleEntrySchema(BaseModel):
    bs_day: int = Field(description="The day of the month in B.S. calendar (1 to 32)")
    location: str = Field(description="The pipeline or location name (e.g., 'old_line', 'new_line', 'पुरानाे लाइन', 'नयाँ लाइन')")
    start_time: str = Field(description="The start time in 24-hour HH:MM format (e.g., '04:00', '20:15')")
    end_time: str = Field(description="The end time in 24-hour HH:MM format (e.g., '05:00', '21:15')")

class ExtractedScheduleSchema(BaseModel):
    bs_year: int = Field(description="The Bikram Sambat (B.S.) year (e.g., 2081)")
    bs_month: int = Field(description="The Bikram Sambat (B.S.) month number (1 to 12). 1=Baishakh, 2=Jestha, 3=Ashadh, 4=Shrawan, 5=Bhadra, 6=Ashwin, 7=Kartik, 8=Mangsir, 9=Poush, 10=Magh, 11=Falgun, 12=Chaitra")
    entries: List[ScheduleEntrySchema] = Field(description="List of schedule entries extracted from the table")

class BaseExtractor(ABC):
    @abstractmethod
    def extract_schedule(self, image_path: str) -> ExtractedScheduleSchema:
        """Extract schedule from an image containing a table."""
        pass

class GeminiExtractor(BaseExtractor):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()
        self.model = model

    def extract_schedule(self, image_path: str) -> ExtractedScheduleSchema:
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
            "For each entry, extract the B.S. day of the month, the location/pipeline name, start time (HH:MM), and end time (HH:MM). "
            "Ensure the time is in 24-hour HH:MM format."
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
