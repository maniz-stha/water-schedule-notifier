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
