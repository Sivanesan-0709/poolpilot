import datetime
from typing import List, Dict, Any, Optional


MONTHLY_HISTORICAL_DATA = {
    "October 2025": {"co2_kg": 24.5, "money_saved": 1420.0, "fuel_saved_l": 16.2, "rides": 8, "km_pooled": 175.0},
    "November 2025": {"co2_kg": 32.0, "money_saved": 1850.0, "fuel_saved_l": 21.4, "rides": 11, "km_pooled": 228.0},
    "December 2025": {"co2_kg": 28.4, "money_saved": 1640.0, "fuel_saved_l": 18.9, "rides": 9, "km_pooled": 202.0},
    "January 2026": {"co2_kg": 38.2, "money_saved": 2180.0, "fuel_saved_l": 25.5, "rides": 13, "km_pooled": 272.0},
    "February 2026": {"co2_kg": 44.0, "money_saved": 2560.0, "fuel_saved_l": 29.3, "rides": 15, "km_pooled": 314.0},
    "March 2026": {"co2_kg": 52.8, "money_saved": 3100.0, "fuel_saved_l": 35.2, "rides": 18, "km_pooled": 377.0}
}

COLLEGE_LEADERBOARD = [
    {
        "rank": 1,
        "college_name": "Rajalakshmi Engineering College (REC)",
        "domain": "rec.ac.in",
        "co2_saved_kg": 1420.0,
        "money_saved_inr": 184000.0,
        "active_commuters": 342,
        "total_pools": 128,
        "trees_equivalent": 71,
        "badge": "🌿 Top Green Campus"
    },
    {
        "rank": 2,
        "college_name": "Anna University (CEG & ACT)",
        "domain": "annauniv.edu",
        "co2_saved_kg": 1280.0,
        "money_saved_inr": 156000.0,
        "active_commuters": 298,
        "total_pools": 112,
        "trees_equivalent": 64,
        "badge": "⚡ Mobility Leader"
    },
    {
        "rank": 3,
        "college_name": "IIT Madras",
        "domain": "iitm.ac.in",
        "co2_saved_kg": 960.0,
        "money_saved_inr": 122000.0,
        "active_commuters": 215,
        "total_pools": 84,
        "trees_equivalent": 48,
        "badge": "🚴 Zero Carbon Champion"
    },
    {
        "rank": 4,
        "college_name": "SRM Institute of Science & Technology",
        "domain": "srmist.edu.in",
        "co2_saved_kg": 840.0,
        "money_saved_inr": 105000.0,
        "active_commuters": 180,
        "total_pools": 72,
        "trees_equivalent": 42,
        "badge": "🚗 Active Pooler"
    },
    {
        "rank": 5,
        "college_name": "SSN College of Engineering",
        "domain": "ssn.edu.in",
        "co2_saved_kg": 720.0,
        "money_saved_inr": 92000.0,
        "active_commuters": 155,
        "total_pools": 61,
        "trees_equivalent": 36,
        "badge": "🌱 Eco Trailblazer"
    }
]


def format_inr_lakhs(amount_inr: float) -> str:
    """Formats Indian Rupee amounts into Lakhs or standard commas."""
    if amount_inr >= 100000.0:
        lakhs = amount_inr / 100000.0
        return f"₹{lakhs:.2f} Lakhs"
    elif amount_inr >= 1000.0:
        return f"₹{int(amount_inr):,}"
    return f"₹{int(amount_inr)}"


def get_personal_impact(user_id: int = 1, selected_month: Optional[str] = None) -> Dict[str, Any]:
    """Returns the personal monthly and total impact stats for a commuter."""
    months = list(MONTHLY_HISTORICAL_DATA.keys())
    if not selected_month or selected_month not in MONTHLY_HISTORICAL_DATA:
        selected_month = months[-1]  # Default to latest month (March 2026)

    m_data = MONTHLY_HISTORICAL_DATA[selected_month]

    # Calculate cumulative lifetime totals
    tot_co2 = sum(v["co2_kg"] for v in MONTHLY_HISTORICAL_DATA.values())
    tot_money = sum(v["money_saved"] for v in MONTHLY_HISTORICAL_DATA.values())
    tot_fuel = sum(v["fuel_saved_l"] for v in MONTHLY_HISTORICAL_DATA.values())
    tot_rides = sum(v["rides"] for v in MONTHLY_HISTORICAL_DATA.values())
    tot_km = sum(v["km_pooled"] for v in MONTHLY_HISTORICAL_DATA.values())

    return {
        "selected_month": selected_month,
        "available_months": months,
        "monthly": {
            "co2_saved_kg": m_data["co2_kg"],
            "money_saved_inr": m_data["money_saved"],
            "money_saved_formatted": format_inr_lakhs(m_data["money_saved"]),
            "fuel_saved_litres": m_data["fuel_saved_l"],
            "rides_pooled": m_data["rides"],
            "km_pooled": m_data["km_pooled"],
            "trees_equivalent": round(m_data["co2_kg"] / 20.0, 1)
        },
        "lifetime": {
            "total_co2_kg": round(tot_co2, 1),
            "total_money_inr": round(tot_money, 0),
            "total_money_formatted": format_inr_lakhs(tot_money),
            "total_fuel_l": round(tot_fuel, 1),
            "total_rides": tot_rides,
            "total_km": round(tot_km, 1),
            "trees_planted_equivalent": round(tot_co2 / 20.0, 1),
            "carbon_neutral_days": int(round(tot_co2 / 1.8))
        },
        "monthly_trend": [
            {"month": k, "co2_kg": v["co2_kg"], "money_saved": v["money_saved"], "rides": v["rides"]}
            for k, v in MONTHLY_HISTORICAL_DATA.items()
        ]
    }


def get_college_impact_cascade(college_domain: str = "rec.ac.in") -> Dict[str, Any]:
    """
    Returns college network collective impact and leaderboard rank.
    """
    matched_cohort = None
    for item in COLLEGE_LEADERBOARD:
        if item["domain"] == college_domain or college_domain in item["domain"]:
            matched_cohort = item
            break

    if not matched_cohort:
        matched_cohort = COLLEGE_LEADERBOARD[0]  # Default to REC

    cascade_banner = (
        f"Your {matched_cohort['college_name']} cohort saved {int(matched_cohort['co2_saved_kg'])} kg CO2, "
        f"{format_inr_lakhs(matched_cohort['money_saved_inr'])} this month — Ranked #{matched_cohort['rank']} in Chennai!"
    )

    user_cohort_dict = dict(matched_cohort)
    user_cohort_dict["money_saved_formatted"] = format_inr_lakhs(matched_cohort["money_saved_inr"])

    formatted_leaderboard = []
    for item in COLLEGE_LEADERBOARD:
        entry = dict(item)
        entry["money_saved_formatted"] = format_inr_lakhs(entry["money_saved_inr"])
        formatted_leaderboard.append(entry)

    return {
        "user_cohort": user_cohort_dict,
        "cascade_banner": cascade_banner,
        "leaderboard": formatted_leaderboard,
        "total_chennai_co2_kg": sum(c["co2_saved_kg"] for c in COLLEGE_LEADERBOARD),
        "total_chennai_money_formatted": format_inr_lakhs(sum(c["money_saved_inr"] for c in COLLEGE_LEADERBOARD)),
        "total_active_student_commuters": sum(c["active_commuters"] for c in COLLEGE_LEADERBOARD)
    }
