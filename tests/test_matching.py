import pytest
from app.matching import match_rider_with_rides, parse_time_minutes, calculate_reliability_score, calculate_detour_score
from app.models import User, Ride


class MockUser:
    def __init__(self, id, name, gender, trust_score=80, is_id_verified=True, is_member=False, on_time_rate=95.0, completion_rate=98.0, cancellation_rate=2.0, complaints_count=0):
        self.id = id
        self.name = name
        self.gender = gender
        self.trust_score = trust_score
        self.is_id_verified = is_id_verified
        self.is_member = is_member
        self.avg_rating = 4.8
        self.on_time_rate = on_time_rate
        self.completion_rate = completion_rate
        self.cancellation_rate = cancellation_rate
        self.complaints_count = complaints_count
        self.reports_count = 0
        self.trust_badge = "Gold" if trust_score >= 80 else "Silver"
        self.emergency_contacts = [{"name": "Mom", "phone": "9840000000"}]


class MockRide:
    def __init__(
        self,
        id,
        driver,
        origin_name,
        dest_name,
        polyline,
        dist_km,
        dur_min,
        dept_time="08:30",
        avail_seats=3,
        price_per_km=6.0,
        women_only=False
    ):
        self.id = id
        self.driver = driver
        self.driver_id = driver.id
        self.origin_name = origin_name
        self.destination_name = dest_name
        self.route_polyline = polyline
        self.route_distance_km = dist_km
        self.route_duration_min = dur_min
        self.departure_time = dept_time
        self.available_seats = avail_seats
        self.total_seats = 4
        self.price_per_km = price_per_km
        self.is_women_only = women_only
        self.status = "open"


def test_matching_partial_route_and_6_factor_breakdown():
    polyline = [
        [12.8288, 80.2184],  # Siruseri
        [12.8475, 80.2264],  # Navalur
        [12.9010, 80.2279],  # Sholinganallur
        [12.9174, 80.2307],  # Karapakkam
        [12.9654, 80.2461]   # Perungudi
    ]
    driver = MockUser(3, "Karthik", "male", trust_score=95)
    ride = MockRide(1, driver, "Siruseri", "Perungudi", polyline, 16.0, 35.0, dept_time="08:30")

    rider = MockUser(1, "Rahul", "male")
    res = match_rider_with_rides(
        rider_user=rider,
        pickup_name="Sholinganallur",
        pickup_lat=12.9010,
        pickup_lng=80.2279,
        drop_name="Karapakkam",
        drop_lat=12.9174,
        drop_lng=80.2307,
        departure_time="08:45",
        seats_needed=1,
        available_rides=[ride]
    )

    assert res["success"] is True
    assert res["matches_count"] == 1
    match = res["matches"][0]
    assert match["ride_id"] == 1
    assert match["match_score"] >= 70.0
    assert "candidate_filtering_summary" in res
    assert "score_breakdown" in match
    breakdown = match["score_breakdown"]
    assert "route_score" in breakdown
    assert "time_score" in breakdown
    assert "detour_score" in breakdown
    assert "cost_score" in breakdown
    assert "safety_score" in breakdown
    assert "reliability_score" in breakdown


def test_matching_reverse_direction_rejected():
    polyline = [
        [12.8288, 80.2184],
        [12.9010, 80.2279],
        [12.9654, 80.2461]
    ]
    driver = MockUser(3, "Karthik", "male")
    ride = MockRide(1, driver, "Siruseri", "Perungudi", polyline, 16.0, 35.0)

    rider = MockUser(1, "Rahul", "male")
    res = match_rider_with_rides(
        rider_user=rider,
        pickup_name="Perungudi",
        pickup_lat=12.9654,
        pickup_lng=80.2461,
        drop_name="Siruseri",
        drop_lat=12.8288,
        drop_lng=80.2184,
        departure_time="08:30",
        seats_needed=1,
        available_rides=[ride]
    )
    assert res["matches_count"] == 0
    assert res["fallback_advice"] is not None
    assert "direction" in res["candidate_filtering_summary"].lower()


def test_matching_women_only_filtering():
    polyline = [[12.9830, 80.2594], [12.9010, 80.2279], [12.8288, 80.2184]]
    female_driver = MockUser(4, "Ananya", "female", trust_score=90)
    male_driver = MockUser(3, "Karthik", "male", trust_score=95)

    women_ride = MockRide(1, female_driver, "Thiruvanmiyur", "Siruseri", polyline, 18.0, 40.0, women_only=True)
    general_ride = MockRide(2, male_driver, "Thiruvanmiyur", "Siruseri", polyline, 18.0, 40.0, women_only=False)

    male_rider = MockUser(1, "Rahul", "male")
    female_rider = MockUser(2, "Priya", "female")

    res_male = match_rider_with_rides(
        rider_user=male_rider,
        pickup_name="Thiruvanmiyur",
        pickup_lat=12.9830,
        pickup_lng=80.2594,
        drop_name="Siruseri",
        drop_lat=12.8288,
        drop_lng=80.2184,
        departure_time="08:30",
        available_rides=[women_ride, general_ride]
    )
    assert res_male["matches_count"] == 1
    assert res_male["matches"][0]["ride_id"] == 2

    res_female = match_rider_with_rides(
        rider_user=female_rider,
        pickup_name="Thiruvanmiyur",
        pickup_lat=12.9830,
        pickup_lng=80.2594,
        drop_name="Siruseri",
        drop_lat=12.8288,
        drop_lng=80.2184,
        departure_time="08:30",
        women_only_filter=True,
        available_rides=[women_ride, general_ride]
    )
    assert res_female["matches_count"] == 1
    assert res_female["matches"][0]["ride_id"] == 1


def test_matching_seat_capacity():
    polyline = [[12.9249, 80.1197], [13.0067, 80.2025], [13.0418, 80.2341]]
    driver = MockUser(3, "Karthik", "male")
    ride = MockRide(1, driver, "Tambaram", "T Nagar", polyline, 18.0, 40.0, avail_seats=1)

    rider = MockUser(1, "Rahul", "male")
    res = match_rider_with_rides(
        rider_user=rider,
        pickup_name="Tambaram",
        pickup_lat=12.9249,
        pickup_lng=80.1197,
        drop_name="T Nagar",
        drop_lat=13.0418,
        drop_lng=80.2341,
        departure_time="08:30",
        seats_needed=2,
        available_rides=[ride]
    )
    assert res["matches_count"] == 0
    assert "seats" in res["candidate_filtering_summary"].lower()
