import pytest
from app.trusted_circle import generate_trip_token, format_whatsapp_share_url, evaluate_route_deviation


def test_token_generation():
    token1 = generate_trip_token()
    token2 = generate_trip_token()
    assert len(token1) >= 16
    assert token1 != token2


def test_whatsapp_share_url_format():
    url = format_whatsapp_share_url(
        token="tok_test_123",
        rider_name="Rahul",
        origin_name="Tambaram",
        destination_name="REC",
        driver_name="Karthik",
        vehicle_number="TN 09 AB 1234"
    )
    assert url.startswith("https://wa.me/?text=")
    assert "tok_test_123" in url
    assert "Rahul" in url
    assert "Karthik" in url


def test_route_deviation_detection():
    # Polyline from point A to point B
    polyline = [[12.9249, 80.1197], [12.9654, 80.2461]]

    # 1. Coordinate directly on line -> No deviation
    on_route = evaluate_route_deviation(12.9249, 80.1197, polyline)
    assert on_route["is_deviated"] is False
    assert on_route["deviation_distance_m"] <= 50.0

    # 2. Coordinate 1.5 km away from route -> Deviation detected (> 200m)
    off_route = evaluate_route_deviation(12.9000, 80.1197, polyline)
    assert off_route["is_deviated"] is True
    assert off_route["deviation_distance_m"] > 200.0
    assert len(off_route["alert_messages"]) > 0
