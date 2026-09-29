from typing import Dict, Any

# Benchmark Chennai Auto Fare (Government/Market rates): Rs 30 base (first 1.5 km) + Rs 14/km thereafter
AUTO_BASE_FARE = 30.0
AUTO_BASE_KM = 1.5
AUTO_PER_KM_RATE = 14.0

# PoolPilot Peer-to-Peer Pricing
POOL_BASE_FARE = 25.0
POOL_DEFAULT_PER_KM = 6.0
MIN_POOL_FARE = 25.0

# Commission Rates
STANDARD_COMMISSION_RATE = 0.10  # 10% for non-members
MEMBER_COMMISSION_RATE = 0.05    # 5% for Verified Trust Members

# Membership & Rewards
MEMBERSHIP_MONTHLY_FEE = 49.0    # Rs 49 / month
REFERRAL_BONUS = 20.0            # Rs 20 wallet credit


def calculate_auto_fare(distance_km: float) -> float:
    """Calculate benchmark Chennai auto fare for a given distance."""
    if distance_km <= AUTO_BASE_KM:
        return AUTO_BASE_FARE
    extra_km = distance_km - AUTO_BASE_KM
    return round(AUTO_BASE_FARE + (extra_km * AUTO_PER_KM_RATE), 1)


def calculate_pool_fare(
    distance_km: float,
    rate_per_km: float = POOL_DEFAULT_PER_KM,
    seats: int = 1,
    is_multi_rider: bool = False,
    is_member: bool = False
) -> Dict[str, Any]:
    """
    Computes fair ride-pooling fare, savings vs auto, commission, and driver payout.
    Guarantees pool fare is significantly cheaper than commercial autos.
    """
    dist = max(0.5, float(distance_km))
    rate = max(4.0, min(12.0, float(rate_per_km or POOL_DEFAULT_PER_KM)))

    # Raw fare = max(min_fare, distance * per_km_rate)
    raw_fare = max(MIN_POOL_FARE, dist * rate)

    # Multi-rider sharing discount (15% cheaper when sharing with co-passengers)
    if is_multi_rider:
        raw_fare *= 0.85

    # Multiply by seats booked
    seat_multiplier = max(1, seats)
    if seat_multiplier > 1:
        # Additional seats get a 20% discount on the extra seat
        raw_fare = raw_fare + (raw_fare * 0.8 * (seat_multiplier - 1))

    # Auto benchmark
    auto_fare = calculate_auto_fare(dist) * seat_multiplier

    # Safety ceiling: Pool fare must be capped strictly below auto fare (at least 30% cheaper)
    max_allowed = auto_fare * 0.70
    final_fare = round(min(raw_fare, max_allowed), 1)
    final_fare = max(MIN_POOL_FARE * seat_multiplier, final_fare)

    # Ensure savings
    savings = round(max(10.0, auto_fare - final_fare), 1)

    # Commission
    comm_rate = MEMBER_COMMISSION_RATE if is_member else STANDARD_COMMISSION_RATE
    commission = round(final_fare * comm_rate, 2)
    driver_payout = round(final_fare - commission, 2)

    # CO2 saved in kg: 0.12 kg per passenger-km avoided private car trip
    co2_saved = round(dist * seat_multiplier * 0.12, 2)

    return {
        "fare_amount": final_fare,
        "auto_fare_estimate": auto_fare,
        "savings_amount": savings,
        "savings_percent": round((savings / auto_fare) * 100.0, 1) if auto_fare > 0 else 50.0,
        "commission_rate": comm_rate,
        "commission_amount": commission,
        "driver_payout": driver_payout,
        "co2_saved_kg": co2_saved,
        "distance_km": round(dist, 2)
    }
