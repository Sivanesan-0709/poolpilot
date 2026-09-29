import re
import datetime
from typing import Dict, Any, List
from app.routing import snap_point_to_polyline

# Regex for Indian vehicle plates (e.g. TN 09 AB 1234, TN-09-AB-1234, TN09AB1234, TN 22 C 5678)
VEHICLE_PLATE_REGEX = re.compile(r"^[A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9]{3,4}$", re.IGNORECASE)


def validate_vehicle_plate(plate: str) -> bool:
    """Validate Indian motor vehicle registration plate format."""
    if not plate:
        return False
    clean = plate.strip().upper()
    return bool(VEHICLE_PLATE_REGEX.match(clean))


def calculate_trust_score(
    is_id_verified: bool,
    is_phone_verified: bool,
    is_org_verified: bool,
    avg_rating: float,
    total_rides: int,
    cancellations: int,
    reports_count: int,
    is_member: bool = False
) -> Dict[str, Any]:
    """
    Computes holistic 0-100 Trust Score and determines Trust Badge tier.
    """
    score = 30  # Baseline

    if is_id_verified:
        score += 25
    if is_phone_verified:
        score += 10
    if is_org_verified:
        score += 15

    # Rating contribution (up to +15 pts for 5-star)
    if avg_rating and avg_rating >= 3.0:
        score += int(round((avg_rating - 3.0) * 7.5))

    # Experience bonus (+1 pt per completed trip, max 10)
    score += min(10, total_rides)

    # Membership trust boost (+5 pts)
    if is_member:
        score += 5

    # Penalties
    score -= (cancellations * 5)
    score -= (reports_count * 15)

    # Clamp to [0, 100]
    final_score = max(0, min(100, score))

    if final_score >= 80:
        badge = "Gold"
        color = "#F59E0B"
    elif final_score >= 50:
        badge = "Silver"
        color = "#9CA3AF"
    else:
        badge = "Bronze"
        color = "#CD7F32"

    return {
        "trust_score": final_score,
        "trust_badge": badge,
        "badge_color": color,
        "is_id_verified": is_id_verified,
        "is_phone_verified": is_phone_verified,
        "is_org_verified": is_org_verified,
        "is_member": is_member
    }


def check_route_deviation(
    current_lat: float,
    current_lng: float,
    route_polyline: List[List[float]],
    threshold_meters: float = 500.0
) -> Dict[str, Any]:
    """
    Checks if vehicle has deviated beyond the safety threshold (default 500 meters)
    from the planned route polyline.
    """
    if not route_polyline or len(route_polyline) < 2:
        return {"is_deviated": False, "deviation_meters": 0.0, "threshold_meters": threshold_meters}

    snap = snap_point_to_polyline(current_lat, current_lng, route_polyline)
    dist_m = snap.get("distance_m", 0.0)

    is_deviated = dist_m > threshold_meters
    return {
        "is_deviated": is_deviated,
        "deviation_meters": round(dist_m, 1),
        "threshold_meters": threshold_meters,
        "snapped_lat": snap.get("snapped_lat"),
        "snapped_lng": snap.get("snapped_lng"),
        "alert_message": (
            f"Safety Alert: Vehicle has deviated {round(dist_m)}m from planned route!"
            if is_deviated else "On planned route"
        )
    }


def is_night_ride(departure_time_str: str) -> bool:
    """
    Detects if the scheduled departure is during night hours (9:00 PM - 5:00 AM).
    Supports ISO datetimes or HH:MM strings.
    """
    if not departure_time_str:
        return False
    try:
        # Check if contains time
        if "T" in departure_time_str:
            time_part = departure_time_str.split("T")[1][:5]
        elif " " in departure_time_str:
            time_part = departure_time_str.split(" ")[1][:5]
        else:
            time_part = departure_time_str[:5]

        hour = int(time_part.split(":")[0])
        # 21 (9 PM) to 23 (11 PM) or 0 to 4 (until 5 AM)
        return hour >= 21 or hour < 5
    except Exception:
        return False


def detect_abuse_or_fraud(user) -> Dict[str, Any]:
    """Flags high-cancellation or frequently reported accounts."""
    flags = []
    total_trips = getattr(user, "total_rides", 0)
    cancellations = getattr(user, "cancellations", 0)
    reports = getattr(user, "reports_count", 0)

    if (total_trips + cancellations) >= 3:
        canc_rate = cancellations / float(total_trips + cancellations)
        if canc_rate > 0.35:
            flags.append(f"High cancellation rate ({int(canc_rate * 100)}%)")

    if reports >= 2:
        flags.append(f"Received {reports} safety/behavior reports")

    return {
        "is_flagged": len(flags) > 0,
        "risk_level": "High" if len(flags) > 1 else ("Medium" if flags else "Normal"),
        "flags": flags
    }
