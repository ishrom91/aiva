"""Tests for anonymization utilities."""

from datetime import datetime

from src.utils.anonymization import (
    extract_time_metadata,
    generate_client_hash,
    round_location_to_district,
)


def test_generate_client_hash_is_deterministic() -> None:
    first = generate_client_hash(12345, "test-salt")
    second = generate_client_hash(12345, "test-salt")
    assert first == second
    assert len(first) == 64


def test_generate_client_hash_differs_by_salt() -> None:
    first = generate_client_hash(12345, "salt-a")
    second = generate_client_hash(12345, "salt-b")
    assert first != second


def test_round_location_to_district() -> None:
    assert round_location_to_district(55.751244, 37.618423) == "55.75,37.62"


def test_extract_time_metadata() -> None:
    dt = datetime(2026, 8, 11, 14, 30)
    metadata = extract_time_metadata(dt)
    assert metadata["hour"] == 14
    assert metadata["day_of_week"] == "tuesday"
    assert metadata["time_of_day"] == "afternoon"
