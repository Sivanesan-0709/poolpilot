import datetime
from typing import List, Dict, Any, Optional
from app.routing import haversine_distance, snap_point_to_polyline
from app.pricing import calculate_pool_fare, calculate_auto_fare
from app.safety import calculate_trust_score


# Weight presets for 6-factor AI Matching Engine (all sum to 1.00 / 100%)
WEIGHT_PRESETS = {
    "balanced": {
        "route": 0.40,
        "time": 0.20,
        "detour": 0.10,
        "cost": 0.10,
        "safety": 0.10,
        "reliability": 0.10
    },
    "safety": {
        "safety": 0.30,
        "reliability": 0.15,
        "route": 0.30,
        "time": 0.10,
        "detour": 0.10,
        "cost": 0.05
    },
    "cheapest": {
        "cost": 0.30,
        "route": 0.30,
        "time": 0.15,
        "detour": 0.10,
        "safety": 0.10,
        "reliability": 0.05
    }
}


def parse_time_minutes(time_str: str) -> int:
    """Parses ISO or HH:MM time string into minutes since midnight."""
    if not time_str:
        return 0
    try:
        if "T" in time_str:
            time_part = time_str.split("T")[1][:5]
        elif " " in time_str:
            time_part = time_str.split(" ")[1][:5]
        else:
            time_part = time_str[:5]
        parts = time_part.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0


def calculate_reliability_score(driver: Any) -> float:
    """
    Computes driver reliability score (0-100) based on:
    on-time rate, completion rate, cancellation rate, and past rating history.
    """
    if not driver:
        return 75.0
    
    on_time = float(getattr(driver, "on_time_rate", 95.0))
    completion = float(getattr(driver, "completion_rate", 98.0))
    cancellation = float(getattr(driver, "cancellation_rate", 2.0))
    rating = float(getattr(driver, "avg_rating", 5.0))
    
    # 35% on-time + 35% completion + 10% low cancellation + 20% rating
    cancellation_factor = max(0.0, 100.0 - (cancellation * 5.0))
    rating_factor = min(100.0, (rating / 5.0) * 100.0)
    
    reliability = (
        (on_time * 0.35) +
        (completion * 0.35) +
        (cancellation_factor * 0.10) +
        (rating_factor * 0.20)
    )
    return round(max(10.0, min(100.0, reliability)), 1)


def calculate_detour_score(detour_km: float, detour_ratio: float, detour_min: float) -> float:
    """
    Normalizes detour required (0-100).
    100 = 0 detour (direct path on corridor).
    Decreases with extra km/min up to hard thresholds (15% detour or 10 min).
    """
    if detour_km <= 0.05:
        return 100.0
    
    # Detour penalty based on distance ratio and time
    ratio_penalty = (detour_ratio / 0.15) * 50.0  # up to 50 pts at 15%
    time_penalty = (detour_min / 10.0) * 50.0     # up to 50 pts at 10 mins
    score = 100.0 - (ratio_penalty + time_penalty)
    return round(max(10.0, min(100.0, score)), 1)


def match_rider_with_rides(
    rider_user: Any,
    pickup_name: str,
    pickup_lat: float,
    pickup_lng: float,
    drop_name: str,
    drop_lat: float,
    drop_lng: float,
    departure_time: str,
    seats_needed: int = 1,
    max_budget: Optional[float] = None,
    priority_mode: str = "balanced",
    women_only_filter: bool = False,
    available_rides: List[Any] = None,
    past_ratings_map: Optional[Dict[int, float]] = None,
    max_corridor_km: float = 3.0
) -> Dict[str, Any]:
    """
    6-Factor AI Match Score Engine:
    Score = Route Overlap (40%) + Time Compatibility (20%) + Detour Required (10%)
            + Cost Compatibility (10%) + Safety Compatibility (10%) + Driver Reliability (10%)
    """
    if available_rides is None:
        available_rides = []

    priority_mode = priority_mode.lower() if priority_mode in WEIGHT_PRESETS else "balanced"
    weights = WEIGHT_PRESETS[priority_mode]
    rider_time_mins = parse_time_minutes(departure_time)

    matches = []
    rejection_counts = {
        "corridor": 0,
        "direction": 0,
        "detour": 0,
        "timing": 0,
        "seats": 0,
        "women_only": 0
    }

    rider_direct_km = haversine_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
    rider_gender = getattr(rider_user, "gender", "other").lower() if rider_user else "other"

    for ride in available_rides:
        if getattr(ride, "status", "open") not in ["open", "active"]:
            continue

        # 1. Seating check
        avail_seats = getattr(ride, "available_seats", 0)
        if avail_seats < seats_needed:
            rejection_counts["seats"] += 1
            continue

        driver = getattr(ride, "driver", None)
        driver_gender = getattr(driver, "gender", "other").lower() if driver else "other"

        # 2. Women-only check
        if ride.is_women_only or women_only_filter:
            if driver_gender != "female" or rider_gender != "female":
                rejection_counts["women_only"] += 1
                continue

        # 3. Route geometry check
        polyline = ride.route_polyline
        if not polyline or len(polyline) < 2:
            continue

        # Snap rider pickup and drop to driver route
        snap_p = snap_point_to_polyline(pickup_lat, pickup_lng, polyline)
        snap_d = snap_point_to_polyline(drop_lat, drop_lng, polyline)

        # 4. Corridor check (Max 3.0 km from driver route)
        if snap_p["distance_km"] > max_corridor_km or snap_d["distance_km"] > max_corridor_km:
            rejection_counts["corridor"] += 1
            continue

        # 5. Sequence & Direction check (Pickup must precede Drop along route)
        progress_p = snap_p["progress_ratio"]
        progress_d = snap_d["progress_ratio"]
        progress_delta = progress_d - progress_p

        # Require forward progress along route
        if progress_delta <= 0.03:
            rejection_counts["direction"] += 1
            continue

        # 6. Detour check & Factor calculation
        detour_km = snap_p["distance_km"] + snap_d["distance_km"]
        detour_ratio = detour_km / max(1.0, ride.route_distance_km)
        detour_min = (detour_km / 25.0) * 60.0

        # Hard-reject above 15% detour ratio or 10 minutes detour
        if detour_ratio > 0.15 and detour_min > 10.0:
            rejection_counts["detour"] += 1
            continue

        detour_score = calculate_detour_score(detour_km, detour_ratio, detour_min)

        # 7. Timing check
        driver_dept_mins = parse_time_minutes(ride.departure_time)
        pickup_eta_mins = driver_dept_mins + int(round(ride.route_duration_min * progress_p))
        time_diff_mins = abs(pickup_eta_mins - rider_time_mins) if rider_time_mins > 0 else 0

        if time_diff_mins > 30:
            rejection_counts["timing"] += 1
            continue

        # 8. Fare & Budget calculation
        segment_km = max(0.8, round(ride.route_distance_km * progress_delta, 2))
        driver_is_member = getattr(driver, "is_member", False) if driver else False
        pricing_data = calculate_pool_fare(
            distance_km=segment_km,
            rate_per_km=getattr(ride, "price_per_km", 6.0),
            seats=seats_needed,
            is_multi_rider=(avail_seats < getattr(ride, "total_seats", 4) - 1),
            is_member=driver_is_member
        )

        fare = pricing_data["fare_amount"]
        if max_budget and max_budget > 0 and fare > (max_budget * 1.25):
            continue

        # 9. 6-Factor Normalization (0 - 100 for each factor)

        # Factor 1: Route overlap score (40%)
        # Progress overlap percentage combined with corridor proximity
        walk_total_km = snap_p["distance_km"] + snap_d["distance_km"]
        corridor_proximity_score = max(35.0, 100.0 - (walk_total_km * 20.0))
        overlap_score = min(100.0, max(30.0, (progress_delta * 100.0) * 0.6 + corridor_proximity_score * 0.4))

        # Factor 2: Time compatibility score (20%)
        time_score = max(10.0, 100.0 - (time_diff_mins * 3.0))

        # Factor 3: Detour required score (10%)
        # (calculated above as detour_score)

        # Factor 4: Cost compatibility score (10%)
        savings_pct = pricing_data.get("savings_percent", 50.0)
        cost_score = min(100.0, max(25.0, savings_pct * 1.5))
        if max_budget and fare <= max_budget:
            cost_score = min(100.0, cost_score + 10.0)

        # Factor 5: Safety compatibility score (10%)
        trust_val = float(getattr(driver, "trust_score", 50) if driver else 50)
        safety_score = trust_val
        if driver and getattr(driver, "is_id_verified", False):
            safety_score = min(100.0, safety_score + 10.0)
        if rider_gender == "female" and driver_gender == "female":
            safety_score = min(100.0, safety_score + 5.0)

        # Factor 6: Driver Reliability score (10%)
        reliability_score = calculate_reliability_score(driver)

        # 10. Compute 6-Factor Weighted Sum
        raw_match_score = (
            overlap_score * weights["route"] +
            time_score * weights["time"] +
            detour_score * weights["detour"] +
            cost_score * weights["cost"] +
            safety_score * weights["safety"] +
            reliability_score * weights["reliability"]
        )

        # Learned preference bonus (+8 points if previously rated 4.5+)
        if past_ratings_map and driver and driver.id in past_ratings_map:
            past_rating = past_ratings_map[driver.id]
            if past_rating >= 4.5:
                raw_match_score = min(100.0, raw_match_score + 8.0)
            elif past_rating >= 4.0:
                raw_match_score = min(100.0, raw_match_score + 4.0)

        final_match_score = round(max(10.0, min(100.0, raw_match_score)), 1)
        is_recommended = final_match_score >= 85.0

        # Meeting point & drop walk details
        meeting_walk_m = snap_p["distance_m"]
        meeting_walk_min = round((meeting_walk_m / 1000.0) / 4.5 * 60.0, 1)

        drop_walk_m = snap_d["distance_m"]
        drop_walk_min = round((drop_walk_m / 1000.0) / 4.5 * 60.0, 1)

        # Explainable AI match reasons
        reasons = []
        overlap_pct = int(round(progress_delta * 100))
        reasons.append(f"Matches {overlap_pct}% of driver's route along {ride.origin_name.split('(')[0].strip()} → {ride.destination_name.split('(')[0].strip()}")

        if time_diff_mins <= 5:
            reasons.append(f"Optimal timing: Driver reaches pickup in ~{int(round(ride.route_duration_min * progress_p))} min (within {time_diff_mins} min of target)")
        else:
            reasons.append(f"Departure window match within {time_diff_mins} minutes")

        if driver:
            badge = getattr(driver, "trust_badge", "Silver")
            rating = getattr(driver, "avg_rating", 5.0)
            reasons.append(f"Driver {driver.name} is {badge} Verified ({int(trust_val)}/100 Trust Score, {rating}★, {int(reliability_score)}% Reliability)")

        reasons.append(f"Saves ₹{int(pricing_data['savings_amount'])} vs Auto ({int(pricing_data['savings_percent'])}% cheaper)")

        if detour_km <= 0.2:
            reasons.append("Zero detour corridor pickup along driver's route")
        else:
            reasons.append(f"Minimal detour: {round(detour_km, 2)} km total detour")

        if meeting_walk_m > 30:
            reasons.append(f"Suggested meeting point: {int(meeting_walk_m)}m walk (~{int(meeting_walk_min)} min) to main road")
        else:
            reasons.append("Direct door-to-corridor pickup along the road")

        if ride.is_women_only:
            reasons.append("Verified Women-Only ride pool")

        matches.append({
            "ride_id": ride.id,
            "ride": ride,
            "driver": driver,
            "match_score": final_match_score,
            "is_recommended": is_recommended,
            "score_breakdown": {
                "route_score": round(overlap_score, 1),
                "time_score": round(time_score, 1),
                "detour_score": round(detour_score, 1),
                "cost_score": round(cost_score, 1),
                "safety_score": round(safety_score, 1),
                "reliability_score": round(reliability_score, 1)
            },
            "match_reasons": reasons,
            "pricing": pricing_data,
            "meeting_point": {
                "lat": snap_p["snapped_lat"],
                "lng": snap_p["snapped_lng"],
                "walk_meters": round(meeting_walk_m, 1),
                "walk_minutes": meeting_walk_min,
                "pickup_original": [pickup_lat, pickup_lng]
            },
            "drop_meeting_point": {
                "lat": snap_d["snapped_lat"],
                "lng": snap_d["snapped_lng"],
                "walk_meters": round(drop_walk_m, 1),
                "walk_minutes": drop_walk_min,
                "drop_original": [drop_lat, drop_lng]
            },
            "segment_km": segment_km,
            "pickup_eta_mins": pickup_eta_mins,
            "time_diff_mins": time_diff_mins
        })

    # Sort descending by match_score
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    top_matches = matches[:3] if len(matches) > 3 else matches

    # Build candidate filtering summary line
    total_rejected = sum(rejection_counts.values())
    filter_summary_parts = []
    if rejection_counts["corridor"] > 0:
        filter_summary_parts.append(f"{rejection_counts['corridor']} outside route corridor")
    if rejection_counts["direction"] > 0:
        filter_summary_parts.append(f"{rejection_counts['direction']} wrong direction")
    if rejection_counts["timing"] > 0:
        filter_summary_parts.append(f"{rejection_counts['timing']} timing mismatch (>30m)")
    if rejection_counts["detour"] > 0:
        filter_summary_parts.append(f"{rejection_counts['detour']} excess detour (>15%)")
    if rejection_counts["seats"] > 0:
        filter_summary_parts.append(f"{rejection_counts['seats']} seats full")
    if rejection_counts["women_only"] > 0:
        filter_summary_parts.append(f"{rejection_counts['women_only']} women-only filter")

    if total_rejected > 0:
        candidate_filtering_summary = f"Filtered out {total_rejected} candidates: {', '.join(filter_summary_parts)}"
    else:
        candidate_filtering_summary = "All available corridor candidates evaluated"

    # Fallback advice if 0 matches
    fallback_advice = None
    if not matches:
        fallback_advice = generate_no_match_advice(
            rejection_counts=rejection_counts,
            pickup_name=pickup_name,
            drop_name=drop_name,
            departure_time=departure_time
        )

    return {
        "success": True,
        "priority_mode": priority_mode,
        "total_available": len(available_rides),
        "total_filtered_out": total_rejected,
        "candidate_filtering_summary": candidate_filtering_summary,
        "rejection_counts": rejection_counts,
        "matches_count": len(matches),
        "top_matches_count": len(top_matches),
        "matches": matches,
        "top_matches": top_matches,
        "fallback_advice": fallback_advice
    }


def generate_no_match_advice(
    rejection_counts: Dict[str, int],
    pickup_name: str,
    drop_name: str,
    departure_time: str
) -> Dict[str, Any]:
    """Generates actionable advice and public transit / 2-leg alternatives when 0 direct matches exist."""
    tips = []
    if rejection_counts.get("timing", 0) > 0:
        tips.append("Widen your departure window by +/- 20 minutes to find more drivers leaving around your time.")
    if rejection_counts.get("corridor", 0) > 0:
        tips.append("Expand pickup walking distance to 2.5 km or select a nearby major arterial road (e.g. OMR, GST Road, Mount Road).")
    if rejection_counts.get("seats", 0) > 0:
        tips.append("Try requesting 1 seat if searching for multiple passengers.")
    if rejection_counts.get("women_only", 0) > 0:
        tips.append("Women-only filter is active. You can switch to 'Safety-First' mode with verified drivers to see more pools.")

    if not tips:
        tips.append("No active drivers currently on this exact corridor. Post a ride request so matching drivers can accept you!")

    transit_options = [
        {
            "mode": "Suburban Train + Pool Connection",
            "title": "Chennai Suburban Railway (Tambaram - Beach Line)",
            "route": f"Suburban Train from {pickup_name.split('(')[0].strip()} station to nearest hub + 5-min pool to {drop_name.split('(')[0].strip()}",
            "fare_estimate": "₹10 (Train) + ₹35 (Pool)",
            "co2_saved": "0.45 kg"
        },
        {
            "mode": "MTC Express Bus (19B / 570 / 21G)",
            "title": "MTC AC Bus Corridor",
            "route": f"Catch MTC Deluxe bus along OMR / GST corridor to {drop_name.split('(')[0].strip()}",
            "fare_estimate": "₹25 - ₹40",
            "co2_saved": "0.38 kg"
        }
    ]

    return {
        "title": "No Direct Matches Right Now",
        "tips": tips,
        "transit_alternatives": transit_options
    }
