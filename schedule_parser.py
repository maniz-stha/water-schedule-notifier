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
