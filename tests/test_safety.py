import pytest
from app.safety import (
    calculate_trust_score,
    check_route_deviation,
    is_night_ride,
    validate_vehicle_plate
)


def test_trust_score_and_badges():
    # New unverified user
    unverified = calculate_trust_score(
        is_id_verified=False,
        is_phone_verified=False,
        is_org_verified=False,
        avg_rating=4.0,
        total_rides=0,
        cancellations=0,
        reports_count=0
    )
    assert unverified["trust_score"] < 50
    assert unverified["trust_badge"] == "Bronze"

    # Verified active user
    gold_user = calculate_trust_score(
        is_id_verified=True,
        is_phone_verified=True,
        is_org_verified=True,
        avg_rating=4.9,
        total_rides=15,
        cancellations=0,
        reports_count=0,
        is_member=True
    )
    assert gold_user["trust_score"] >= 80
    assert gold_user["trust_badge"] == "Gold"

    # Penalized user with cancellations and reports
    penalized = calculate_trust_score(
        is_id_verified=True,
        is_phone_verified=True,
        is_org_verified=False,
        avg_rating=3.2,
        total_rides=5,
        cancellations=4,
        reports_count=2
    )
    assert penalized["trust_score"] < gold_user["trust_score"]


def test_route_deviation_detection():
    # Planned straight line along latitude
    route = [
        [13.0000, 80.2000],
        [13.0100, 80.2000],
        [13.0200, 80.2000]
    ]

    # Point directly on route (<50m)
    on_track = check_route_deviation(13.0050, 80.2000, route, threshold_meters=500.0)
    assert on_track["is_deviated"] is False
    assert on_track["deviation_meters"] < 50.0

    # Point deviated by 800 meters (e.g. 80.2080 longitude offset is ~870m in Chennai)
    deviated = check_route_deviation(13.0050, 80.2080, route, threshold_meters=500.0)
    assert deviated["is_deviated"] is True
    assert deviated["deviation_meters"] > 500.0
    assert "Safety Alert" in deviated["alert_message"]


def test_night_ride_detection():
    # 22:30 is 10:30 PM (night)
    assert is_night_ride("2026-09-29T22:30:00") is True
    assert is_night_ride("23:15") is True
    assert is_night_ride("03:30") is True

    # Day rides
    assert is_night_ride("2026-09-29T09:30:00") is False
    assert is_night_ride("15:00") is False
    assert is_night_ride("18:45") is False


def test_vehicle_plate_validation():
    # Valid Indian plates
    assert validate_vehicle_plate("TN 09 AB 1234") is True
    assert validate_vehicle_plate("TN-09-AB-1234") is True
    assert validate_vehicle_plate("TN22C5678") is True
    assert validate_vehicle_plate("TN 01 Z 9999") is True
    assert validate_vehicle_plate("DL 01 AA 1111") is True

    # Invalid plates
    assert validate_vehicle_plate("INVALID123") is False
    assert validate_vehicle_plate("1234") is False
    assert validate_vehicle_plate("") is False
