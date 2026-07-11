# 💧 Water Schedule Notifier

A smart utility tool that extracts, converts, and alerts you about local water schedules using Google Gemini AI and Telegram.

---

## 📖 Background & Problem Statement

In many areas, water distribution schedules are not fixed to specific days or times. The supplier updates schedules dynamically, often publishing them as images (tables written in Nepali/Devanagari script) on their Facebook page. Keeping track of these schedules manually is error-prone, resulting in missed water distribution slots.

To solve this, **Water Schedule Notifier** allows you to feed schedule images to an AI model that:
1. **Extracts** the schedule details from the image using Google Gemini.
2. **Translates & Converts** the Nepali calendar dates (Bikram Sambat / B.S.) and Devanagari text into standard English and Gregorian dates (A.D.).
3. **Alerts** you via Telegram notifications exactly when your water schedule start time arrives.

---

## ✨ Features

- **AI-Powered Image Ingestion**: Uses Gemini (`gemini-2.0-flash` by default) to read schedule tables from images.
- **Nepali Calendar (B.S.) Parsing**: Translates Nepali month/day and converts dates to the Gregorian (A.D.) calendar format (`YYYY-MM-DD`).
- **Location-based Filtering**: Option to filter and extract schedule entries only for a specific target location (area).
- **Automated Merge & Sort**: Safely integrates new data into your existing `schedule.json` database, preventing duplicate entries and sorting schedules chronologically.
- **Smart Telegram Notifier**: Runs checks for upcoming slots (within the next hour) in the Kathmandu timezone (`Asia/Kathmandu`), waits/sleeps until the exact start time, and dispatches Telegram notifications.
- **Robust Client Retry Logic**: Implements retry strategies for Telegram alerts in case of temporary network timeouts.

---

## 📂 Project Structure

```
water-schedule/
├── config.py             # Loads and validates environment configurations
├── date_converter.py     # Date conversion (B.S. -> A.D.) and location name normalization
├── extractor.py          # Interfaces with Gemini API using Pydantic schema validation
├── ingest_schedule.py    # CLI entry point to ingest and merge schedules from images
├── notifier.py          # CLI entry point to check schedules and send alerts
├── schedule_parser.py    # Filters upcoming schedule slots starting within an hour
├── telegram_client.py    # Sends Markdown-formatted alerts to Telegram with retry support
├── requirements.txt      # Python dependencies
├── schedule.json         # Compiled JSON database of water schedules
├── schedule_format.md    # Description of the JSON schema
└── tests/                # Comprehensive unit tests for all modules
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.9+
- A Telegram Bot token (created via [@BotFather](https://t.me/BotFather)) and your Telegram Chat/Channel ID.
- A Gemini API Key from Google AI Studio.

### 2. Install Dependencies
Set up a virtual environment and install the required libraries:
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
Update the `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
GEMINI_API_KEY=your_gemini_api_key_here
TARGET_LOCATION=your_default_target_location_here
```

---

## 🛠️ Usage

### Ingesting a Schedule from an Image

Pass the path to your downloaded water schedule image to `ingest_schedule.py`:

```bash
# Ingest schedule
python ingest_schedule.py sample_image.jpeg

# Or filter and ingest entries only for a specific target location
python ingest_schedule.py sample_image.jpeg --target-location "Baluwatar"

# Overwrite existing records for the same day instead of merging
python ingest_schedule.py sample_image.jpeg --overwrite
```

### Running the Notifier

Run `notifier.py` regularly (e.g., as an hourly cron job). It will query the schedule database for any slot starting in the Kathmandu timezone within the next hour:

```bash
# Run notifier in dry-run mode (does not sleep or send actual messages)
python notifier.py --dry-run

# Run notifier in production mode
python notifier.py
```

#### Automating the Notifier (Cron Example)
To run the notifier automatically every hour, add a cron job:
```cron
0 * * * * cd /path/to/water-schedule && ./venv/bin/python notifier.py >> notifier.log 2>&1
```

---

## 🧪 Running Tests

A comprehensive suite of unit tests is included. Run it with:

```bash
python -m unittest discover tests
```
