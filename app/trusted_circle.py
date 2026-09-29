import secrets
import urllib.parse
import datetime
from typing import List, Dict, Any, Optional
from app.routing import snap_point_to_polyline, haversine_distance


ALLOWED_RELATIONS = ["Parent", "Friend", "Partner", "College Security", "Emergency Contact", "Sibling", "Family"]


def generate_trip_token() -> str:
    """Generates a cryptographically secure URL-safe token for trip sharing."""
    return secrets.token_urlsafe(16)


def format_whatsapp_share_url(
    token: str,
    rider_name: str,
    origin_name: str,
    destination_name: str,
    driver_name: str,
    vehicle_number: str,
    base_url: str = "http://localhost:8000"
) -> str:
    """
    Constructs a pre-filled WhatsApp share URL for broadcasting live trip status
    to trusted contacts in one click.
    """
    tracking_url = f"{base_url.rstrip('/')}/track/{token}"
    msg = (
        f"🚨 Live PoolPilot Ride Share\n"
        f"Hi! {rider_name} is sharing their live commute from {origin_name} to {destination_name}.\n"
        f"🚗 Driver: {driver_name} ({vehicle_number})\n"
        f"📍 Track real-time GPS & route progress here:\n"
        f"{tracking_url}\n\n"
        f"Protected by PoolPilot Verified Safety Network."
    )
    encoded_text = urllib.parse.quote(msg)
    return f"https://wa.me/?text={encoded_text}"


def evaluate_route_deviation(
    current_lat: float,
    current_lng: float,
    route_polyline: List[List[float]],
    deviation_threshold_m: float = 200.0,
    minutes_stopped: float = 0.0
) -> Dict[str, Any]:
    """
    Checks if vehicle has deviated > 200m from route polyline or stopped > 5 minutes.
    Returns deviation status and alert messages.
    """
    if not route_polyline or len(route_polyline) < 2:
        return {
            "is_deviated": False,
            "deviation_distance_m": 0.0,
            "is_stopped_alert": False,
            "alert_level": "normal",
            "message": "Tracking normal along corridor"
        }

    snap = snap_point_to_polyline(current_lat, current_lng, route_polyline)
    deviation_m = round(snap["distance_m"], 1)

    is_deviated = deviation_m > deviation_threshold_m
    is_stopped_alert = minutes_stopped >= 5.0

    alert_level = "normal"
    alert_messages = []

    if is_deviated:
        alert_level = "critical" if deviation_m > 500 else "warning"
        alert_messages.append(f"Route deviation detected: {int(deviation_m)}m away from scheduled corridor.")

    if is_stopped_alert:
        alert_level = "warning" if alert_level == "normal" else "critical"
        alert_messages.append(f"Vehicle stationary for {int(minutes_stopped)} minutes in active trip.")

    if not alert_messages:
        alert_messages.append(f"On track: within {int(deviation_m)}m of route.")

    return {
        "is_deviated": is_deviated,
        "deviation_distance_m": deviation_m,
        "is_stopped_alert": is_stopped_alert,
        "alert_level": alert_level,
        "alert_messages": alert_messages,
        "snapped_lat": snap["snapped_lat"],
        "snapped_lng": snap["snapped_lng"],
        "progress_ratio": snap["progress_ratio"]
    }
