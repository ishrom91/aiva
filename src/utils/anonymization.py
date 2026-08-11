"""Anonymization utilities for Aiva AI Bot."""

import hashlib
from datetime import datetime


def generate_client_hash(telegram_id: int, salt: str) -> str:
    """Generate a SHA-256 hash for a client's telegram ID using the provided salt."""
    payload = f"{telegram_id}:{salt}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def round_location_to_district(lat: float, lon: float) -> str:
    """Round latitude and longitude to district level (2 decimal places)."""
    return f"{lat:.2f},{lon:.2f}"


def extract_time_metadata(dt: datetime) -> dict:
    """Extract time-related metadata from a datetime object."""
    hour = dt.hour
    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 22:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    return {
        "hour": hour,
        "day_of_week": dt.strftime("%A").lower(),
        "time_of_day": time_of_day,
    }
