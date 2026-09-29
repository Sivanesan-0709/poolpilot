import pytest
from app.impact import get_personal_impact, get_college_impact_cascade, format_inr_lakhs


def test_inr_lakh_formatting():
    assert format_inr_lakhs(184000.0) == "₹1.84 Lakhs"
    assert format_inr_lakhs(50000.0) == "₹50,000"
    assert format_inr_lakhs(850.0) == "₹850"


def test_personal_impact_calculation():
    impact = get_personal_impact(user_id=1, selected_month="March 2026")
    assert impact["selected_month"] == "March 2026"
    assert "monthly" in impact
    assert "lifetime" in impact
    assert impact["monthly"]["co2_saved_kg"] > 0
    assert impact["monthly"]["money_saved_inr"] > 0
    assert len(impact["monthly_trend"]) == 6


def test_college_impact_cascade():
    cascade = get_college_impact_cascade(college_domain="rec.ac.in")
    assert "REC" in cascade["cascade_banner"] or "Rajalakshmi" in cascade["cascade_banner"]
    assert len(cascade["leaderboard"]) >= 5
    assert cascade["leaderboard"][0]["rank"] == 1
