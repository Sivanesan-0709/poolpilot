import pytest
from app.pricing import (
    calculate_pool_fare,
    calculate_auto_fare,
    STANDARD_COMMISSION_RATE,
    MEMBER_COMMISSION_RATE
)


def test_pricing_auto_fare_benchmark():
    # 1.5 km or less = base 30
    assert calculate_auto_fare(1.0) == 30.0
    assert calculate_auto_fare(1.5) == 30.0
    # 10 km = 30 + (8.5 * 14) = 30 + 119 = 149
    assert calculate_auto_fare(10.0) == 149.0


def test_pricing_cap_below_auto():
    # Pool fare must always be strictly below auto fare with significant savings
    for dist in [2.0, 5.0, 10.0, 20.0, 30.0]:
        pricing = calculate_pool_fare(distance_km=dist, rate_per_km=6.0)
        auto_f = pricing["auto_fare_estimate"]
        pool_f = pricing["fare_amount"]
        savings = pricing["savings_amount"]

        assert pool_f < auto_f
        assert savings > 0
        assert pricing["savings_percent"] >= 30.0  # At least 30% cheaper


def test_pricing_commission_rates():
    # Standard user commission = 10%
    standard_calc = calculate_pool_fare(distance_km=10.0, is_member=False)
    assert standard_calc["commission_rate"] == STANDARD_COMMISSION_RATE
    assert standard_calc["commission_amount"] == round(standard_calc["fare_amount"] * 0.10, 2)

    # Verified Trust Member commission = 5%
    member_calc = calculate_pool_fare(distance_km=10.0, is_member=True)
    assert member_calc["commission_rate"] == MEMBER_COMMISSION_RATE
    assert member_calc["commission_amount"] == round(member_calc["fare_amount"] * 0.05, 2)
    assert member_calc["driver_payout"] > standard_calc["driver_payout"]


def test_pricing_multi_rider_discount():
    single = calculate_pool_fare(distance_km=12.0, is_multi_rider=False)
    multi = calculate_pool_fare(distance_km=12.0, is_multi_rider=True)

    assert multi["fare_amount"] <= single["fare_amount"]
