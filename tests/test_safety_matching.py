import pytest
from app.safety_matching import check_driver_safety_criteria, apply_safety_filter


class MockDriver:
    def __init__(self, id=1, name="Driver A", is_id_verified=True, college="REC", gender="male", rating=4.8, complaints=0, emergency_contacts=None):
        self.id = id
        self.name = name
        self.is_id_verified = is_id_verified
        self.college_company = college
        self.gender = gender
        self.avg_rating = rating
        self.complaints_count = complaints
        self.reports_count = 0
        self.emergency_contacts = emergency_contacts or [{"name": "Contact", "phone": "9840000000"}]


class MockRider:
    def __init__(self, id=2, name="Rider B", college="REC", gender="male"):
        self.id = id
        self.name = name
        self.college_company = college
        self.gender = gender


def test_safety_criteria_checks():
    driver = MockDriver(is_id_verified=True, college="REC", gender="female", rating=4.8, complaints=0)
    rider = MockRider(college="REC", gender="female")

    # Pass all criteria
    res = check_driver_safety_criteria(
        driver=driver,
        rider=rider,
        safety_prefs={
            "verified_id_only": True,
            "same_org_only": True,
            "same_gender_only": True,
            "min_driver_rating": 4.5,
            "zero_complaints_only": True
        }
    )
    assert res["passed"] is True
    assert len(res["failed_criteria"]) == 0

    # Fail rating criteria
    res_fail_rating = check_driver_safety_criteria(
        driver=driver,
        rider=rider,
        safety_prefs={"min_driver_rating": 4.9}
    )
    assert res_fail_rating["passed"] is False
    assert "min_rating" in res_fail_rating["failed_criteria"]


def test_apply_safety_filter_and_relaxation():
    driver1 = MockDriver(id=1, rating=4.2, is_id_verified=True)
    driver2 = MockDriver(id=2, rating=4.9, is_id_verified=True)
    rider = MockRider()

    matches = [
        {"ride_id": 101, "driver": driver1, "match_score": 88.0},
        {"ride_id": 102, "driver": driver2, "match_score": 94.0}
    ]

    # Filter with min_driver_rating = 4.5 (Driver 1 excluded, Driver 2 included)
    res = apply_safety_filter(matches, rider, safety_prefs={"min_driver_rating": 4.5})
    assert res["filtered_count"] == 1
    assert res["filtered_matches"][0]["ride_id"] == 102

    # Filter with min_driver_rating = 5.0 (0 matches remain, generates relaxation suggestion)
    res_zero = apply_safety_filter(matches, rider, safety_prefs={"min_driver_rating": 5.0})
    assert res_zero["filtered_count"] == 0
    assert len(res_zero["relaxation_suggestions"]) >= 1
    assert "Relax rating filter" in res_zero["relaxation_suggestions"][0]["message"]
