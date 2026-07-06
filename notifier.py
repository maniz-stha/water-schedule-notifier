import json
import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from config import load_config
from telegram_client import send_telegram_message
from schedule_parser import find_slots_starting_in_hour

def run_notifications(schedule_data: dict, current_time: datetime, bot_token: str, chat_id: str, dry_run=False):
    """Find matching slots, sleep if needed, and send notifications."""
    slots = find_slots_starting_in_hour(schedule_data, current_time)
    if not slots:
        print("No water schedule slots starting within the next hour.")
        return

    for slot in slots:
        delay = slot["delay_seconds"]
        if delay > 0:
            if dry_run:
                print(f"[Dry Run] Would sleep for {delay} seconds until slot start time {slot['start_time']}")
            else:
                print(f"Sleeping for {delay} seconds until slot start time {slot['start_time']}...")
                time.sleep(delay)
            
        message = (
            f"**Water Alert - {slot['date']}**\n"
            f"Pipeline: {slot['pipeline']}\n"
            f"Start: {slot['start_time']}\n"
            f"End: {slot['end_time']}"
        )
        
        if dry_run:
            print(f"[Dry Run] Sending Telegram message:\n{message}\n")
        else:
            print(f"Sending alert for {slot['pipeline']} pipeline...")
            success = send_telegram_message(bot_token, chat_id, message)
            if success:
                print("Alert sent successfully!")
            else:
                print("Failed to send alert.")

def main():
    dry_run = "--dry-run" in sys.argv
    
    bot_token = "dummy_token"
    chat_id = "dummy_chat_id"
    if not dry_run:
        try:
            config = load_config()
            bot_token = config["TELEGRAM_BOT_TOKEN"]
            chat_id = config["TELEGRAM_CHAT_ID"]
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
        bot_token=bot_token,
        chat_id=chat_id,
        dry_run=dry_run
    )

if __name__ == "__main__":
    main()
