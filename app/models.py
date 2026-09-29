import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(120), nullable=True)
    role = Column(String(20), default="rider")  # rider, driver, both, admin
    gender = Column(String(20), default="other")  # male, female, other
    college_company = Column(String(120), nullable=True)

    # Trust & Verification
    is_id_verified = Column(Boolean, default=False)
    id_doc_filename = Column(String(255), nullable=True)
    selfie_filename = Column(String(255), nullable=True)
    is_phone_verified = Column(Boolean, default=True)
    is_org_verified = Column(Boolean, default=False)
    is_member = Column(Boolean, default=False)  # Verified Trust Membership
    membership_expiry = Column(DateTime, nullable=True)

    trust_score = Column(Integer, default=50)  # 0-100
    wallet_balance = Column(Float, default=150.0)  # Mock wallet credits in INR
    referral_code = Column(String(20), unique=True, index=True)
    referred_by = Column(String(20), nullable=True)

    # Reputation & History
    total_rides = Column(Integer, default=0)
    cancellations = Column(Integer, default=0)
    reports_count = Column(Integer, default=0)
    rating_sum = Column(Float, default=5.0)
    rating_count = Column(Integer, default=1)

    # Reliability metrics
    on_time_rate = Column(Float, default=95.0)  # percentage 0-100
    completion_rate = Column(Float, default=98.0)  # percentage 0-100
    cancellation_rate = Column(Float, default=2.0)  # percentage 0-100
    complaints_count = Column(Integer, default=0)

    # Emergency & Trusted Contacts
    emergency_contacts_json = Column(Text, default="[]")
    trusted_contacts_json = Column(Text, default="[]")

    # Safety Preferences
    safety_preferences_json = Column(Text, default="{}")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    driver_profile = relationship("DriverProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    rides_offered = relationship("Ride", back_populates="driver")
    bookings = relationship("Booking", back_populates="rider")

    @property
    def avg_rating(self) -> float:
        if self.rating_count <= 0:
            return 5.0
        return round(self.rating_sum / self.rating_count, 1)

    @property
    def trust_badge(self) -> str:
        if self.trust_score >= 80:
            return "Gold"
        elif self.trust_score >= 50:
            return "Silver"
        return "Bronze"

    @property
    def emergency_contacts(self):
        try:
            return json.loads(self.emergency_contacts_json) if self.emergency_contacts_json else []
        except Exception:
            return []

    @emergency_contacts.setter
    def emergency_contacts(self, value):
        self.emergency_contacts_json = json.dumps(value if value else [])

    @property
    def trusted_contacts(self):
        try:
            return json.loads(self.trusted_contacts_json) if self.trusted_contacts_json else []
        except Exception:
            return []

    @trusted_contacts.setter
    def trusted_contacts(self, value):
        self.trusted_contacts_json = json.dumps(value if value else [])

    @property
    def safety_preferences(self):
        try:
            return json.loads(self.safety_preferences_json) if self.safety_preferences_json else {}
        except Exception:
            return {}

    @safety_preferences.setter
    def safety_preferences(self, value):
        self.safety_preferences_json = json.dumps(value if value else {})


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    vehicle_number = Column(String(30), nullable=False)  # e.g., TN 09 AB 1234
    vehicle_model = Column(String(100), nullable=False)  # e.g., Swift Dzire (Silver)
    total_seats = Column(Integer, default=4)
    license_number = Column(String(50), default="DL-TN-2024-MOCK")
    is_verified_driver = Column(Boolean, default=False)

    user = relationship("User", back_populates="driver_profile")


class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    origin_name = Column(String(150), nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)

    destination_name = Column(String(150), nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)

    departure_time = Column(String(50), nullable=False)  # ISO string or HH:MM
    available_seats = Column(Integer, default=3)
    total_seats = Column(Integer, default=4)
    price_per_km = Column(Float, default=6.0)
    is_women_only = Column(Boolean, default=False)

    # Route details
    route_polyline_json = Column(Text, default="[]")  # JSON list of [lat, lng]
    route_distance_km = Column(Float, default=0.0)
    route_duration_min = Column(Float, default=0.0)
    status = Column(String(30), default="open")  # open, active, in_progress, completed, cancelled
    is_offline_routing = Column(Boolean, default=False)
    recurring_days_json = Column(Text, nullable=True)  # e.g. '["Mon","Tue","Wed","Thu","Fri"]'

    # Live position tracking for polling & fallback
    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)
    last_deviation_m = Column(Float, default=0.0)
    sos_active = Column(Boolean, default=False)
    last_updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    driver = relationship("User", back_populates="rides_offered")
    bookings = relationship("Booking", back_populates="ride", cascade="all, delete-orphan")

    @property
    def route_polyline(self):
        try:
            return json.loads(self.route_polyline_json) if self.route_polyline_json else []
        except Exception:
            return []

    @route_polyline.setter
    def route_polyline(self, val):
        self.route_polyline_json = json.dumps(val if val else [])

    @property
    def recurring_days(self):
        try:
            return json.loads(self.recurring_days_json) if self.recurring_days_json else []
        except Exception:
            return []

    @recurring_days.setter
    def recurring_days(self, val):
        self.recurring_days_json = json.dumps(val if val else [])


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"), nullable=False)
    rider_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    pickup_name = Column(String(150), nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)

    drop_name = Column(String(150), nullable=False)
    drop_lat = Column(Float, nullable=False)
    drop_lng = Column(Float, nullable=False)

    # Dynamic meeting point & walking geometry
    meeting_point_lat = Column(Float, nullable=True)
    meeting_point_lng = Column(Float, nullable=True)
    meeting_point_walk_m = Column(Float, default=0.0)
    meeting_point_walk_min = Column(Float, default=0.0)

    drop_meeting_lat = Column(Float, nullable=True)
    drop_meeting_lng = Column(Float, nullable=True)
    drop_walk_m = Column(Float, default=0.0)

    seats_booked = Column(Integer, default=1)
    fare_amount = Column(Float, default=0.0)
    auto_fare_estimate = Column(Float, default=0.0)
    savings_amount = Column(Float, default=0.0)
    commission_amount = Column(Float, default=0.0)
    driver_payout = Column(Float, default=0.0)

    status = Column(String(30), default="requested")  # requested, confirmed, driver_arriving, in_progress, completed, cancelled
    otp_code = Column(String(10), default="1234")
    priority_mode = Column(String(30), default="balanced")
    match_score = Column(Float, default=90.0)

    # AI explanations & breakdowns
    match_reasons_json = Column(Text, default="[]")
    score_breakdown_json = Column(Text, default="{}")

    payment_status = Column(String(30), default="pending")  # pending, paid_wallet, paid_upi
    tracking_token = Column(String(64), unique=True, index=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    ride = relationship("Ride", back_populates="bookings")
    rider = relationship("User", back_populates="bookings")

    @property
    def match_reasons(self):
        try:
            return json.loads(self.match_reasons_json) if self.match_reasons_json else []
        except Exception:
            return []

    @match_reasons.setter
    def match_reasons(self, val):
        self.match_reasons_json = json.dumps(val if val else [])

    @property
    def score_breakdown(self):
        try:
            return json.loads(self.score_breakdown_json) if self.score_breakdown_json else {}
        except Exception:
            return {}

    @score_breakdown.setter
    def score_breakdown(self, val):
        self.score_breakdown_json = json.dumps(val if val else {})


class RideReview(Base):
    __tablename__ = "ride_reviews"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Float, default=5.0)
    comment = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # sos, deviation, safe_drop_ok, safe_drop_issue, anonymous_report, night_mode
    details_json = Column(Text, default="{}")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def details(self):
        try:
            return json.loads(self.details_json) if self.details_json else {}
        except Exception:
            return {}

    @details.setter
    def details(self, val):
        self.details_json = json.dumps(val if val else {})


class TripShareToken(Base):
    __tablename__ = "trip_share_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    ride_id = Column(Integer, ForeignKey("rides.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CollegePool(Base):
    __tablename__ = "college_pools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    college_name = Column(String(150), nullable=False)
    college_domain = Column(String(100), default="rec.ac.in")
    origin_zone = Column(String(100), nullable=False)
    destination_zone = Column(String(100), nullable=False)
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    departure_time = Column(String(50), nullable=False)
    time_window = Column(String(50), default="7:30 - 8:30 AM")
    direction = Column(String(30), default="home_to_college")  # home_to_college, college_to_home
    days_json = Column(Text, default='["Mon","Tue","Wed","Thu","Fri"]')
    host_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    member_ids_json = Column(Text, default="[]")
    total_seats = Column(Integer, default=4)
    available_seats = Column(Integer, default=3)
    fare_per_seat = Column(Float, default=45.0)
    original_fare = Column(Float, default=55.0)
    notices_json = Column(Text, default="[]")
    status = Column(String(30), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def days(self):
        try:
            return json.loads(self.days_json) if self.days_json else []
        except Exception:
            return []

    @days.setter
    def days(self, val):
        self.days_json = json.dumps(val if val else [])

    @property
    def member_ids(self):
        try:
            return json.loads(self.member_ids_json) if self.member_ids_json else []
        except Exception:
            return []

    @member_ids.setter
    def member_ids(self, val):
        self.member_ids_json = json.dumps(val if val else [])

    @property
    def notices(self):
        try:
            return json.loads(self.notices_json) if self.notices_json else []
        except Exception:
            return []

    @notices.setter
    def notices(self, val):
        self.notices_json = json.dumps(val if val else [])


class HistoricalDemand(Base):
    __tablename__ = "historical_demand"

    id = Column(Integer, primary_key=True, index=True)
    zone_name = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    hour_of_day = Column(Integer, nullable=False)  # 0 to 23
    day_of_week = Column(String(20), default="Weekday")
    request_count = Column(Integer, default=1)
    density = Column(Float, default=1.0)
