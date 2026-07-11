# AI Water Schedule Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate AI-based table extraction from a Nepali water schedule image (B.S. calendar), convert the dates and locations to A.D. and standardised values, and merge the parsed schedule into the existing schedule database.

**Architecture:** We introduce a modular extractor interface (`BaseExtractor`) and a Google GenAI SDK implementation (`GeminiExtractor`). We also implement a calendar translation layer using `nepali-datetime` to convert Bikram Sambat dates to Gregorian dates, and a CLI script `ingest_schedule.py` to orchestrate extraction, conversion, normalization, and database merging.

**Tech Stack:** Python 3.13, Google GenAI SDK (`google-genai`), `nepali-datetime`, Pydantic, Pillow.

## Global Constraints
- System environment must use the Python 3.13 virtual environment located in `venv/`.
- All unit tests must be self-contained and run offline, mocking the Google GenAI SDK and PIL image calls.
- Preserving existing code structure and configurations unless explicitly modified by tasks.

---

### Task 1: Setup Dependencies

**Files:**
- Create: `requirements.txt`

**Interfaces:**
- Consumes: None
- Produces: Installed python packages in virtual environment

- [ ] **Step 1: Create `requirements.txt`**

Write the dependency requirements to `requirements.txt`.
```python
# requirements.txt
google-genai==0.1.1
nepali-datetime==1.5.0
pydantic>=2.0.0
pillow>=10.0.0
```

- [ ] **Step 2: Install dependencies**

Run the installation command in the virtual environment.
Run: `./venv/bin/pip install -r requirements.txt`
Expected: Successful package installations of google-genai, nepali-datetime, pydantic, and pillow.

- [ ] **Step 3: Commit dependency files**

Run:
```bash
git add requirements.txt
git commit -m "chore: add project requirements for AI integration"
```

---

### Task 2: Configure Environment and Config Management

**Files:**
- Modify: `config.py:1-33`
- Modify: `.env.example:1-2`

**Interfaces:**
- Consumes: `.env` environment variables
- Produces: `load_ai_config()` returning `dict` with keys `GEMINI_API_KEY`, `GEMINI_MODEL`

- [ ] **Step 1: Write failing test for config update**

Add a test block to `tests/test_config.py`.
```python
# Append to tests/test_config.py
    def test_load_ai_config_success(self):
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-123", "GEMINI_MODEL": "gemini-2.0-flash"}):
            config = load_config() # Make sure standard load doesn't break
            ai_config = notifier.load_config.load_ai_config() # (Will implement as load_ai_config in config.py)

    def test_load_ai_config_missing_key(self):
        with mock.patch.dict("os.environ", {}):
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
            from config import load_ai_config
            with self.assertRaises(ValueError):
                load_ai_config(env_file=None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m unittest tests/test_config.py`
Expected: FAIL with `ImportError: cannot import name 'load_ai_config' from 'config'`

- [ ] **Step 3: Implement `load_ai_config` in `config.py`**

Modify `config.py` to add `load_ai_config`.
```python
# config.py (adding load_ai_config at the end)
def load_ai_config(env_file=".env"):
    """Load and validate AI credentials from the environment."""
    if env_file:
        load_env_file(env_file)
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("Missing required environment variable: GEMINI_API_KEY")
    return {
        "GEMINI_API_KEY": gemini_api_key,
        "GEMINI_MODEL": os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    }
```

- [ ] **Step 4: Update `.env.example`**

Modify `.env.example` to append `GEMINI_API_KEY`.
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
GEMINI_API_KEY=your_gemini_api_key
```

- [ ] **Step 5: Verify tests pass**

Run: `./venv/bin/python -m unittest tests/test_config.py`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
```bash
git add config.py .env.example tests/test_config.py
git commit -m "feat: add load_ai_config helper and update environment config"
```

---

### Task 3: Implement Bikram Sambat Date Converter

**Files:**
- Create: `date_converter.py`
- Create: `tests/test_date_converter.py`

**Interfaces:**
- Consumes: `bs_year` (int), `bs_month` (int), `bs_day` (int), and raw location string (str)
- Produces: `convert_bs_to_ad(bs_year: int, bs_month: int, bs_day: int) -> str` (returns YYYY-MM-DD), `normalize_location(raw_location: str) -> str` (returns normalized key)

- [ ] **Step 1: Write tests for date conversion and location normalization**

Create `tests/test_date_converter.py`.
```python
import unittest
from date_converter import convert_bs_to_ad, normalize_location

class TestDateConverter(unittest.TestCase):
    def test_convert_bs_to_ad_valid(self):
        # 2081 Shrawan 1 BS -> 2024-07-16 AD
        ad_str = convert_bs_to_ad(2081, 4, 1)
        self.assertEqual(ad_str, "2024-07-16")
        
    def test_convert_bs_to_ad_invalid(self):
        with self.assertRaises(ValueError):
            convert_bs_to_ad(2081, 13, 1)

    def test_normalize_location(self):
        self.assertEqual(normalize_location("पुरानाे लाइन"), "old_line")
        self.assertEqual(normalize_location("पुरानो लाइन"), "old_line")
        self.assertEqual(normalize_location("old line"), "old_line")
        self.assertEqual(normalize_location("नयाँ लाइन"), "new_line")
        self.assertEqual(normalize_location("नया लाइन"), "new_line")
        self.assertEqual(normalize_location("new line"), "new_line")
        self.assertEqual(normalize_location("Random Pipeline"), "Random Pipeline")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m unittest tests/test_date_converter.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'date_converter'`

- [ ] **Step 3: Implement `date_converter.py`**

Create `date_converter.py`.
```python
import nepali_datetime
from datetime import date
from typing import Dict

def convert_bs_to_ad(bs_year: int, bs_month: int, bs_day: int) -> str:
    """
    Convert a Bikram Sambat (B.S.) date to a Gregorian (A.D.) date string in YYYY-MM-DD format.
    Raises ValueError if the date is invalid or out of range.
    """
    try:
        bs_date = nepali_datetime.date(bs_year, bs_month, bs_day)
        ad_date = bs_date.to_datetime_date()
        return ad_date.strftime("%Y-%m-%d")
    except Exception as e:
        raise ValueError(f"Failed to convert B.S. date {bs_year}-{bs_month}-{bs_day} to A.D.: {e}")

def normalize_location(raw_location: str) -> str:
    """
    Normalize location names to match the schedule format ('old_line' or 'new_line').
    """
    loc = raw_location.strip().lower()
    if loc in ["पुरानाे लाइन", "पुरानो line", "old line", "old_line", "old", "पुरानाे", "पुरानो"]:
        return "old_line"
    elif loc in ["नयाँ लाइन", "नया line", "new line", "new_line", "new", "नयाँ", "नया"]:
        return "new_line"
    return raw_location
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./venv/bin/python -m unittest tests/test_date_converter.py`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add date_converter.py tests/test_date_converter.py
git commit -m "feat: add Bikram Sambat date converter and location normalizer"
```

---

### Task 4: Implement AI Extractor Module

**Files:**
- Create: `extractor.py`
- Create: `tests/test_extractor.py`

**Interfaces:**
- Consumes: Path to image (str)
- Produces: `BaseExtractor` and `GeminiExtractor(BaseExtractor)` returning `ExtractedScheduleSchema`

- [ ] **Step 1: Write test mocking GenAI client**

Create `tests/test_extractor.py`.
```python
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
        self.assertEqual(result.entries[0].location, "पुरानाे LINE")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m unittest tests/test_extractor.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'extractor'`

- [ ] **Step 3: Implement `extractor.py`**

Create `extractor.py`.
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./venv/bin/python -m unittest tests/test_extractor.py`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add extractor.py tests/test_extractor.py
git commit -m "feat: add BaseExtractor and GeminiExtractor implementation with schema"
```

---

### Task 5: Implement Ingester Command Line Script

**Files:**
- Create: `ingest_schedule.py`
- Create: `tests/test_ingest.py`

**Interfaces:**
- Consumes: CLI args: image path, optional --overwrite, optional --env-file, optional --schedule-json
- Produces: Merges extracted schedules into schedule JSON database, sorted by start_time.

- [ ] **Step 1: Write test for merge and ingest orchestration**

Create `tests/test_ingest.py`.
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m unittest tests/test_ingest.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'ingest_schedule'`

- [ ] **Step 3: Implement `ingest_schedule.py`**

Create `ingest_schedule.py`.
```python
import argparse
import json
import os
import sys
from config import load_ai_config
from extractor import GeminiExtractor
from date_converter import convert_bs_to_ad, normalize_location

def merge_schedules(existing_schedule: dict, new_schedule: dict, overwrite: bool = False) -> dict:
    merged = existing_schedule.copy()
    for date_str, pipelines in new_schedule.items():
        if overwrite or date_str not in merged:
            merged[date_str] = pipelines
        else:
            for pipeline, slots in pipelines.items():
                merged[date_str][pipeline] = slots
                
    for date_str in merged:
        for pipeline in merged[date_str]:
            merged[date_str][pipeline].sort(key=lambda s: s.get("start_time", ""))
            
    return merged

def process_image(image_path: str, overwrite: bool, env_file: str, schedule_json_path: str):
    try:
        config = load_ai_config(env_file)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Extracting schedule from {image_path} using {config['GEMINI_MODEL']}...")
    extractor = GeminiExtractor(api_key=config["GEMINI_API_KEY"], model=config["GEMINI_MODEL"])
    try:
        extracted = extractor.extract_schedule(image_path)
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    new_schedule_data = {}
    converted_count = 0
    skipped_count = 0
    
    for entry in extracted.entries:
        try:
            ad_date = convert_bs_to_ad(extracted.bs_year, extracted.bs_month, entry.bs_day)
            norm_loc = normalize_location(entry.location)
            
            if ad_date not in new_schedule_data:
                new_schedule_data[ad_date] = {}
            if norm_loc not in new_schedule_data[ad_date]:
                new_schedule_data[ad_date][norm_loc] = []
                
            new_schedule_data[ad_date][norm_loc].append({
                "start_time": entry.start_time,
                "end_time": entry.end_time
            })
            converted_count += 1
        except ValueError as e:
            print(f"Warning: Skipping entry due to conversion error: {e}", file=sys.stderr)
            skipped_count += 1
            
    print(f"Successfully processed {converted_count} entries (skipped {skipped_count}).")
    
    existing_schedule = {}
    if os.path.exists(schedule_json_path):
        try:
            with open(schedule_json_path, "r") as f:
                existing_schedule = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load existing schedule from {schedule_json_path}: {e}", file=sys.stderr)
            print("Will start with an empty schedule database.", file=sys.stderr)
            
    merged = merge_schedules(existing_schedule, new_schedule_data, overwrite=overwrite)
    
    try:
        with open(schedule_json_path, "w") as f:
            json.dump(merged, f, indent=4)
        print(f"Successfully updated schedule file at: {schedule_json_path}")
    except Exception as e:
        print(f"Error saving schedule to {schedule_json_path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Ingest water schedule from an image using Gemini.")
    parser.add_argument("image_path", help="Path to the schedule image file.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing schedule dates completely.")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file.")
    parser.add_argument("--schedule-json", default="schedule.json", help="Path to the schedule.json file.")
    args = parser.parse_args()
    
    process_image(args.image_path, args.overwrite, args.env_file, args.schedule_json)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./venv/bin/python -m unittest tests/test_ingest.py`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `./venv/bin/python -m unittest discover tests`
Expected: PASS all tests (14+ tests total)

- [ ] **Step 6: Commit**

Run:
```bash
git add ingest_schedule.py tests/test_ingest.py
git commit -m "feat: implement ingest_schedule command line script and verification tests"
```

---

## Verification Plan

### Automated Tests
- Run: `./venv/bin/python -m unittest discover tests`
Expected: All tests pass.

### Manual Verification
1. Setup a valid `GEMINI_API_KEY` in `.env`.
2. Provide a sample image of a water schedule in Devanagari script.
3. Run the ingest script:
   `./venv/bin/python ingest_schedule.py <path_to_sample_image>.png`
4. Inspect `schedule.json` to verify that B.S. dates were converted to correct A.D. dates and merged correctly.
