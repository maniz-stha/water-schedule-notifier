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
    if loc in ["पुरानाे लाइन", "पुरानो लाइन", "old line", "old_line", "old", "पुरानाे", "पुरानो"]:
        return "old_line"
    elif loc in ["नयाँ लाइन", "नया लाइन", "new line", "new_line", "new", "नयाँ", "नया"]:
        return "new_line"
    return raw_location
