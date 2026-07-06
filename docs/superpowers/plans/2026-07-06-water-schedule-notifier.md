# Water Schedule Notifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a zero-dependency, Cron-friendly Python script that reads a water schedule, checks for active slots in the `Asia/Kathmandu` timezone, sleeps until the start times, and alerts via Telegram.

**Architecture:** A single-file python script (`notifier.py`) triggered hourly by system Cron. It parses `schedule.json`, determines start times in `Asia/Kathmandu` within the current hour, sleeps if needed, and uses Python's standard `urllib.request` to send Telegram notifications.

**Tech Stack:** Python 3.9+ (utilizing the built-in `zoneinfo` module for timezone handling), standard library `unittest` for testing.

## Global Constraints
- Target timezone: `Asia/Kathmandu`
- Trigger interval: Hourly (top of the hour)
- Zero external dependencies (use standard library modules only: `json`, `datetime`, `zoneinfo`, `urllib.request`, `os`, `time`, `unittest`)

---

### Task 1: Project Setup & Configuration Loading

**Files:**
- Create: `config.py`
- Create: `.env`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` class / configuration loading functions that read variables from environment.

- [ ] **Step 1: Write the failing test for configuration loading**
  Create `tests/test_config.py` containing:
  ```python
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
          config = load_config()
          self.assertEqual(config["TELEGRAM_BOT_TOKEN"], "test-token")
          self.assertEqual(config["TELEGRAM_CHAT_ID"], "test-chat-id")

      @mock.patch.dict(os.environ, {}, clear=True)
      def test_load_config_missing_keys(self):
          with self.assertRaises(ValueError) as ctx:
              load_config()
          self.assertIn("Missing required environment variables", str(ctx.exception))
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/test_config.py`
  Expected: FAIL (ModuleNotFoundError: No module named 'config')

- [ ] **Step 3: Implement `config.py`**
  Create `config.py` with standard library code to load env variables:
  ```python
  import os

  def load_env_file(filepath=".env"):
      """Load key-value pairs from a .env file into os.environ if it exists."""
      if os.path.exists(filepath):
          with open(filepath, "r") as f:
              for line in f:
                  line = line.strip()
                  if line and not line.startswith("#") and "=" in line:
                      key, val = line.split("=", 1)
                      os.environ[key.strip()] = val.strip()

  def load_config():
      """Load and validate credentials from the environment."""
      load_env_file()
      bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
      chat_id = os.environ.get("TELEGRAM_CHAT_ID")
      
      missing = []
      if not bot_token:
          missing.append("TELEGRAM_BOT_TOKEN")
      if not chat_id:
          missing.append("TELEGRAM_CHAT_ID")
          
      if missing:
          raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
          
      return {
          "TELEGRAM_BOT_TOKEN": bot_token,
          "TELEGRAM_CHAT_ID": chat_id
      }
  ```

- [ ] **Step 4: Create template `.env`**
  Create `.env` file containing placeholders:
  ```env
  TELEGRAM_BOT_TOKEN=your_bot_token_here
  TELEGRAM_CHAT_ID=your_chat_id_here
  ```

- [ ] **Step 5: Run tests to verify they pass**
  Run: `python -m unittest tests/test_config.py`
  Expected: PASS

- [ ] **Step 6: Commit**
  Run:
  ```bash
  git add config.py .env tests/test_config.py
  git commit -m "feat: add configuration loading and tests"
  ```

---

### Task 2: Telegram Client

**Files:**
- Create: `telegram_client.py`
- Create: `tests/test_telegram_client.py`

**Interfaces:**
- Consumes: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- Produces: `send_telegram_message(token, chat_id, text) -> bool`

- [ ] **Step 1: Write tests for the Telegram client**
  Create `tests/test_telegram_client.py` using `urllib.request` mock:
  ```python
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
          mock_urlopen.return_value = mock_response
          
          success = send_telegram_message("token", "chat", "test alert")
          self.assertTrue(success)
          mock_urlopen.assert_called_once()

      @mock.patch("urllib.request.urlopen")
      def test_send_message_failure_retries(self, mock_urlopen):
          # Simulate URLError for 3 consecutive attempts
          mock_urlopen.side_effect = URLError("Network timeout")
          success = send_telegram_message("token", "chat", "test alert")
          self.assertFalse(success)
          self.assertEqual(mock_urlopen.call_count, 3)
  ```

- [ ] **Step 2: Run tests to verify they fail**
  Run: `python -m unittest tests/test_telegram_client.py`
  Expected: FAIL (ModuleNotFoundError: No module named 'telegram_client')

- [ ] **Step 3: Implement `telegram_client.py`**
  Create `telegram_client.py` using standard HTTP POST requests with retries:
  ```python
  import json
  import time
  import urllib.request
  from urllib.error import URLError

  def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
      """Send message to Telegram channel/chat using urllib.request with retries."""
      url = f"https://api.telegram.org/bot{token}/sendMessage"
      payload = {
          "chat_id": chat_id,
          "text": text,
          "parse_mode": "Markdown"
      }
      data = json.dumps(payload).encode("utf-8")
      req = urllib.request.Request(
          url,
          data=data,
          headers={"Content-Type": "application/json"}
      )
      
      max_retries = 3
      for attempt in range(max_retries):
          try:
              with urllib.request.urlopen(req, timeout=10) as response:
                  res_data = json.loads(response.read().decode("utf-8"))
                  if res_data.get("ok"):
                      return True
          except Exception as e:
              print(f"Attempt {attempt + 1} failed: {e}")
              if attempt < max_retries - 1:
                  time.sleep(2)
      return False
  ```

- [ ] **Step 4: Run tests to verify they pass**
  Run: `python -m unittest tests/test_telegram_client.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add telegram_client.py tests/test_telegram_client.py
  git commit -m "feat: implement telegram notification client with retry logic"
  ```

---

### Task 3: Schedule Parser & Matching Logic

**Files:**
- Create: `schedule_parser.py`
- Create: `tests/test_schedule_parser.py`

**Interfaces:**
- Produces: `find_slots_starting_in_hour(schedule_data, check_datetime) -> list`

- [ ] **Step 1: Write tests for schedule parsing and window matching**
  Create `tests/test_schedule_parser.py`:
  ```python
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
  ```

- [ ] **Step 2: Run tests to verify they fail**
  Run: `python -m unittest tests/test_schedule_parser.py`
  Expected: FAIL (ModuleNotFoundError: No module named 'schedule_parser')

- [ ] **Step 3: Implement `schedule_parser.py`**
  Create `schedule_parser.py` with parsing and math logic:
  ```python
  from datetime import datetime, timedelta
  from zoneinfo import ZoneInfo

  def find_slots_starting_in_hour(schedule_data: dict, check_datetime: datetime) -> list:
      """
      Find all pipeline slots starting in the 1-hour window beginning at check_datetime.
      Returns a list of dicts with: pipeline, start_time, end_time, and delay_seconds.
      """
      kt_tz = ZoneInfo("Asia/Kathmandu")
      # Ensure check_datetime is in Kathmandu timezone
      check_dt = check_datetime.astimezone(kt_tz)
      
      date_str = check_dt.strftime("%Y-%m-%d")
      day_schedule = schedule_data.get(date_str, {})
      
      window_start = check_dt
      window_end = check_dt + timedelta(hours=1)
      
      matching_slots = []
      
      # Pipelines map to their displayed names
      pipelines = {
          "old_line": "Old",
          "new_line": "New"
      }
      
      for key, pipeline_name in pipelines.items():
          slots = day_schedule.get(key, [])
          for slot in slots:
              start_str = slot.get("start_time")
              end_str = slot.get("end_time")
              if not start_str or not end_str:
                  continue
                  
              try:
                  start_h, start_m = map(int, start_str.split(":"))
                  # Construct target datetime for today
                  slot_start_dt = datetime(
                      check_dt.year, check_dt.month, check_dt.day,
                      start_h, start_m, 0, tzinfo=kt_tz
                  )
              except ValueError:
                  continue
                  
              # Check if slot_start_dt falls within [window_start, window_end)
              if window_start <= slot_start_dt < window_end:
                  delay = (slot_start_dt - window_start).total_seconds()
                  matching_slots.append({
                      "pipeline": pipeline_name,
                      "start_time": start_str,
                      "end_time": end_str,
                      "date": date_str,
                      "delay_seconds": max(0.0, delay)
                  })
                  
      # Sort slots by delay_seconds ascending
      matching_slots.sort(key=lambda s: s["delay_seconds"])
      return matching_slots
  ```

- [ ] **Step 4: Run tests to verify they pass**
  Run: `python -m unittest tests/test_schedule_parser.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add schedule_parser.py tests/test_schedule_parser.py
  git commit -m "feat: add schedule parsing and timezone window logic"
  ```

---

### Task 4: Main Execution Runner

**Files:**
- Create: `notifier.py`
- Create: `tests/test_notifier.py`
- Create: `schedule.json`

**Interfaces:**
- Produces: Command line runner `notifier.py` that ties everything together.

- [ ] **Step 1: Write integration tests for the runner**
  Create `tests/test_notifier.py` with mock setups:
  ```python
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
  ```

- [ ] **Step 2: Run tests to verify they fail**
  Run: `python -m unittest tests/test_notifier.py`
  Expected: FAIL (AttributeError: module 'notifier' has no attribute 'run_notifications')

- [ ] **Step 3: Implement `notifier.py`**
  Create `notifier.py` connecting config, parsing, sleep, and Telegram client:
  ```python
  import json
  import os
  import sys
  import time
  from datetime import datetime
  from zoneinfo import ZoneInfo

  from config import load_config
  from telegram_client import send_telegram_message
  from schedule_parser import find_slots_starting_in_hour

  def run_notifications(schedule_data: dict, current_time: datetime, bot_token: str, chat_id: str):
      """Find matching slots, sleep if needed, and send notifications."""
      slots = find_slots_starting_in_hour(schedule_data, current_time)
      if not slots:
          print("No water schedule slots starting within the next hour.")
          return

      for slot in slots:
          delay = slot["delay_seconds"]
          if delay > 0:
              print(f"Sleeping for {delay} seconds until slot start time {slot['start_time']}...")
              time.sleep(delay)
              
          message = (
              f"**Water Alert - {slot['date']}**\n"
              f"Pipeline: {slot['pipeline']}\n"
              f"Start: {slot['start_time']}\n"
              f"End: {slot['end_time']}"
          )
          
          print(f"Sending alert for {slot['pipeline']} pipeline...")
          success = send_telegram_message(bot_token, chat_id, message)
          if success:
              print("Alert sent successfully!")
          else:
              print("Failed to send alert.")

  def main():
      try:
          config = load_config()
      except ValueError as e:
          print(f"Configuration error: {e}")
          sys.exit(1)

      schedule_path = os.path.join(os.path.dirname(__file__), "schedule.json")
      if not os.path.exists(schedule_path):
          print(f"Error: Schedule file not found at {schedule_path}")
          sys.exit(1)

      try:
          with open(schedule_path, "r") as f:
              schedule_data = json.load(f)
      except Exception as e:
          print(f"Error reading schedule.json: {e}")
          sys.exit(1)

      # Determine current time in Kathmandu timezone
      kt_tz = ZoneInfo("Asia/Kathmandu")
      current_time = datetime.now(kt_tz)
      
      run_notifications(
          schedule_data=schedule_data,
          current_time=current_time,
          bot_token=config["TELEGRAM_BOT_TOKEN"],
          chat_id=config["TELEGRAM_CHAT_ID"]
      )

  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 4: Create standard `schedule.json`**
  Create `schedule.json` using the data from `schedule_format.md`:
  ```json
  {
      "2026-07-05": {
          "old_line": [
              {
                  "start_time": "04:00",
                  "end_time": "05:00"
              },
              {
                  "start_time": "20:00",
                  "end_time": "21:00"
              }
          ],
          "new_line": [
              {
                  "start_time": "09:00",
                  "end_time": "21:00"
              }
          ]
      },
      "2026-07-09": {
          "old_line": [
              {
                  "start_time": "04:00",
                  "end_time": "05:00"
              },
              {
                  "start_time": "20:00",
                  "end_time": "21:00"
              }
          ]
      },
      "2026-07-12": {
          "new_line": [
              {
                  "start_time": "07:00",
                  "end_time": "09:00"
              },
              {
                  "start_time": "20:00",
                  "end_time": "21:00"
              }
          ]
      }
  }
  ```

- [ ] **Step 5: Run all tests to verify they pass**
  Run: `python -m unittest discover tests`
  Expected: PASS (all tests run and succeed)

- [ ] **Step 6: Commit**
  Run:
  ```bash
  git add notifier.py tests/test_notifier.py schedule.json
  git commit -m "feat: implement main runner script, mock integration tests, and schedule.json"
  ```

---

### Task 5: Manual End-to-End Verification

**Files:**
- Modify: `schedule.json`
- Modify: `.env`

**Interfaces:**
- Consumes: Real Telegram credentials and customized schedule entries.

- [ ] **Step 1: Set up actual Telegram credentials in `.env`**
  Edit `.env` and fill in `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` with real test credentials. (Do not commit actual secrets!)

- [ ] **Step 2: Add test schedule entry for current time**
  Calculate current time + 1 minute (or current hour top) in `Asia/Kathmandu` timezone, add it to `schedule.json` under today's date.
  For example, if current local time is `2026-07-06 22:40:00`, add a slot for `2026-07-06` starting at `22:41:00`.

- [ ] **Step 3: Run the script manually**
  Run: `python notifier.py`
  Expected: Script prints "Sleeping for X seconds until slot start time...", sleeps, sends message, and you receive the Telegram notification matching the format.

- [ ] **Step 4: Restore `.env` template and delete temp schedule data**
  Revert `.env` and `schedule.json` to their standard, untracked/clean template states.

- [ ] **Step 5: Run automated test suite final check**
  Run: `python -m unittest discover tests`
  Expected: PASS
