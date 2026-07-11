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
        if date_str not in merged:
            merged[date_str] = pipelines
        else:
            for pipeline, slots in pipelines.items():
                if overwrite or pipeline not in merged[date_str]:
                    merged[date_str][pipeline] = slots
                else:
                    existing_slots = merged[date_str][pipeline]
                    for slot in slots:
                        if slot not in existing_slots:
                            existing_slots.append(slot)
                
    for date_str in merged:
        for pipeline in merged[date_str]:
            merged[date_str][pipeline].sort(key=lambda s: s.get("start_time", ""))
            
    # Sort the dictionary by key (date)
    sorted_merged = {k: merged[k] for k in sorted(merged.keys())}
    return sorted_merged

def clean_and_sort_json_file(file_path: str):
    """
    Reads the raw JSON file, combines duplicate keys if they exist,
    sorts the keys, and overwrites the file.
    """
    if not os.path.exists(file_path):
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    def merge_duplicate_keys(pairs):
        res = {}
        for k, v in pairs:
            if k in res:
                if isinstance(res[k], dict) and isinstance(v, dict):
                    for pipeline, slots in v.items():
                        if pipeline not in res[k]:
                            res[k][pipeline] = slots
                        else:
                            existing_slots = res[k][pipeline]
                            for slot in slots:
                                if slot not in existing_slots:
                                    existing_slots.append(slot)
                else:
                    res[k] = v
            else:
                res[k] = v
        return res

    try:
        combined_data = json.loads(content, object_pairs_hook=merge_duplicate_keys)
    except json.JSONDecodeError:
        return

    if isinstance(combined_data, dict):
        for date_str in combined_data:
            if isinstance(combined_data[date_str], dict):
                for pipeline in combined_data[date_str]:
                    if isinstance(combined_data[date_str][pipeline], list):
                        combined_data[date_str][pipeline].sort(key=lambda s: s.get("start_time", ""))
                        
        sorted_data = {k: combined_data[k] for k in sorted(combined_data.keys())}
    else:
        sorted_data = combined_data

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, indent=4, ensure_ascii=False)

def process_image(image_path: str, overwrite: bool, env_file: str, schedule_json_path: str, target_location: str = None):
    try:
        config = load_ai_config(env_file)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
        
    # If target_location is not specified via CLI, fallback to config/env default
    if target_location is None:
        target_location = config.get("TARGET_LOCATION")

        
    print(f"Extracting schedule from {image_path} using {config['GEMINI_MODEL']}...")

    extractor = GeminiExtractor(api_key=config["GEMINI_API_KEY"], model=config["GEMINI_MODEL"])
    try:
        extracted = extractor.extract_schedule(image_path, target_location=target_location)
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    new_schedule_data = {}
    converted_count = 0
    skipped_count = 0
    
    bs_year = extracted.bs_year
    if bs_year <= 0:
        import nepali_datetime
        bs_year = nepali_datetime.date.today().year
        print(f"Year not found in image. Defaulting to current B.S. year: {bs_year}")
        
    for entry in extracted.entries:
        try:
            ad_date = convert_bs_to_ad(bs_year, extracted.bs_month, entry.bs_day)
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
            with open(schedule_json_path, "r", encoding="utf-8") as f:
                existing_schedule = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load existing schedule from {schedule_json_path}: {e}", file=sys.stderr)
            print("Will start with an empty schedule database.", file=sys.stderr)
            
    merged = merge_schedules(existing_schedule, new_schedule_data, overwrite=overwrite)
    
    try:
        with open(schedule_json_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=4, ensure_ascii=False)
        print(f"Successfully updated schedule file at: {schedule_json_path}")
        
        # Run post-write cleanup
        clean_and_sort_json_file(schedule_json_path)
    except Exception as e:
        print(f"Error saving schedule to {schedule_json_path}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Ingest water schedule from an image using Gemini.")
    parser.add_argument("image_path", help="Path to the schedule image file.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing schedule dates completely.")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file.")
    parser.add_argument("--schedule-json", default="schedule.json", help="Path to the schedule.json file.")
    parser.add_argument("--target-location", default=None, help="Only extract schedule entries for rows matching this location name.")
    args = parser.parse_args()
    
    process_image(args.image_path, args.overwrite, args.env_file, args.schedule_json, args.target_location)

if __name__ == "__main__":
    main()
