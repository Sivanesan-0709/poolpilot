import pytest
from app.college_network import verify_college_email, calculate_student_fare, cluster_student_commuters


def test_college_email_verification():
    # Valid REC student email
    rec_res = verify_college_email("student123@rec.ac.in")
    assert rec_res["is_valid"] is True
    assert "Rajalakshmi Engineering College" in rec_res["college_name"]
    assert rec_res["student_discount_pct"] == 15

    # Valid Anna University email
    anna_res = verify_college_email("prof.kumar@annauniv.edu")
    assert anna_res["is_valid"] is True
    assert "Anna University" in anna_res["college_name"]

    # Invalid public email domain
    gmail_res = verify_college_email("user@gmail.com")
    assert gmail_res["is_valid"] is False


def test_student_fare_discount():
    fare_data = calculate_student_fare(100.0, discount_pct=15.0)
    assert fare_data["original_fare"] == 100.0
    assert fare_data["discount_amount"] == 15.0
    assert fare_data["student_fare"] == 85.0


def test_auto_clustering_algorithm():
    # Two students in Tambaram leaving around 7:45 AM
    requests = [
        {"pickup_lat": 12.9249, "pickup_lng": 80.1197, "pickup_name": "Tambaram West", "departure_minutes": 465, "departure_time": "07:45 AM"},
        {"pickup_lat": 12.9280, "pickup_lng": 80.1210, "pickup_name": "Tambaram East", "departure_minutes": 470, "departure_time": "07:50 AM"},
        {"pickup_lat": 13.0850, "pickup_lng": 80.2101, "pickup_name": "Anna Nagar", "departure_minutes": 470, "departure_time": "07:50 AM"}  # Far away
    ]

    clusters = cluster_student_commuters(requests, college_destination="REC", max_distance_km=2.5)
    assert len(clusters) == 1
    assert clusters[0]["members_count"] == 2
