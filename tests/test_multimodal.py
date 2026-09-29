import pytest
from app.multimodal import plan_multimodal_itineraries, find_nearest_stations


def test_nearest_stations_lookup():
    # Near Guindy (13.0067, 80.2025)
    stations = find_nearest_stations(13.0067, 80.2025, max_walk_km=2.0)
    assert len(stations) > 0
    assert any("Guindy" in s["name"] for s in stations)


def test_multimodal_planner_top_3_itineraries():
    # Route from Tambaram to Guindy
    res = plan_multimodal_itineraries(
        origin_lat=12.9249,
        origin_lng=80.1197,
        dest_lat=13.0067,
        dest_lng=80.2025,
        origin_name="Tambaram Railway Station",
        dest_name="Guindy Kathipara Hub",
        priority="fastest"
    )

    assert res["success"] is True
    assert res["itineraries_count"] == 3
    itineraries = res["itineraries"]
    types = [it["itinerary_type"] for it in itineraries]
    assert "multimodal" in types
    assert "direct_carpool" in types
    assert "public_transit" in types

    # Check legs structure
    for it in itineraries:
        assert "legs" in it
        assert len(it["legs"]) >= 1
        assert "total_fare_inr" in it
        assert "total_duration_min" in it
        assert "co2_saved_kg" in it
