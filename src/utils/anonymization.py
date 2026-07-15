import hashlib
from datetime import datetime
from typing import Dict, Tuple


def generate_client_hash(telegram_id: int, salt: str) -> str:
    """
    Generates an irreversible hash from telegram_id.
    Used for logging without PII.
    """
    data = f"{telegram_id}_{salt}".encode()
    return hashlib.sha256(data).hexdigest()


def round_location_to_district(lat: float, lon: float) -> str:
    """
    Rounds coordinates to district level (not exact address).
    """
    lat_rounded = round(lat, 2)
    lon_rounded = round(lon, 2)
    return f"{lat_rounded}_{lon_rounded}"


def extract_time_metadata(timestamp: datetime) -> Dict[str, str]:
    """
    Extracts time metadata (without the actual timestamp).
    """
    time_of_day = (
        "morning" if 6 <= timestamp.hour < 12 else
        "afternoon" if 12 <= timestamp.hour < 18 else
        "evening" if 18 <= timestamp.hour < 22 else "night"
    )
    
    days = ["monday", "tuesday", "wednesday", "thursday", 
            "friday", "saturday", "sunday"]
    
    return {
        "time_of_day": time_of_day,
        "day_of_week": days[timestamp.weekday()],
        "hour": str(timestamp.hour)
    }