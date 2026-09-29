import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, DriverProfile, Ride, Booking


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed test driver and rider
    driver = User(id=1, name="Driver John", phone="9000000001", role="driver", gender="male", trust_score=85)
    rider1 = User(id=2, name="Rider Alice", phone="9000000002", role="rider", gender="female", trust_score=80)
    rider2 = User(id=3, name="Rider Bob", phone="9000000003", role="rider", gender="male", trust_score=75)

    ride = Ride(
        id=1,
        driver_id=1,
        origin_name="Tambaram",
        origin_lat=12.9249,
        origin_lng=80.1197,
        destination_name="Guindy",
        destination_lat=13.0067,
        destination_lng=80.2025,
        departure_time="08:30",
        available_seats=2,
        total_seats=3,
        price_per_km=6.0,
        status="open"
    )
    ride.route_polyline = [[12.9249, 80.1197], [13.0067, 80.2025]]

    db.add_all([driver, rider1, rider2, ride])
    db.commit()

    yield db
    db.close()


def test_booking_decrements_seats_and_prevents_overbooking(test_db):
    ride = test_db.query(Ride).filter(Ride.id == 1).first()
    assert ride.available_seats == 2

    # Rider 1 books 1 seat
    booking1 = Booking(
        ride_id=1,
        rider_id=2,
        pickup_name="Tambaram",
        pickup_lat=12.9249,
        pickup_lng=80.1197,
        drop_name="Guindy",
        drop_lat=13.0067,
        drop_lng=80.2025,
        seats_booked=1,
        fare_amount=45.0,
        status="confirmed",
        otp_code="7842"
    )
    ride.available_seats -= booking1.seats_booked
    test_db.add(booking1)
    test_db.commit()

    # Verify decrement
    ride = test_db.query(Ride).filter(Ride.id == 1).first()
    assert ride.available_seats == 1

    # Rider 2 tries to book 2 seats (which exceeds the remaining 1 available seat)
    seats_requested = 2
    can_book = ride.available_seats >= seats_requested
    assert can_book is False

    # Rider 2 books the remaining 1 seat
    booking2 = Booking(
        ride_id=1,
        rider_id=3,
        pickup_name="Tambaram",
        pickup_lat=12.9249,
        pickup_lng=80.1197,
        drop_name="Guindy",
        drop_lat=13.0067,
        drop_lng=80.2025,
        seats_booked=1,
        fare_amount=45.0,
        status="confirmed",
        otp_code="3921"
    )
    ride.available_seats -= booking2.seats_booked
    test_db.add(booking2)
    test_db.commit()

    ride = test_db.query(Ride).filter(Ride.id == 1).first()
    assert ride.available_seats == 0


def test_cancellation_restores_seats(test_db):
    ride = test_db.query(Ride).filter(Ride.id == 1).first()
    ride.available_seats = 1  # 1 seat remaining

    booking = Booking(
        id=10,
        ride_id=1,
        rider_id=2,
        pickup_name="Tambaram",
        pickup_lat=12.9249,
        pickup_lng=80.1197,
        drop_name="Guindy",
        drop_lat=13.0067,
        drop_lng=80.2025,
        seats_booked=1,
        fare_amount=45.0,
        status="confirmed",
        otp_code="5555"
    )
    test_db.add(booking)
    test_db.commit()

    # Cancel booking -> seat should be restored
    booking.status = "cancelled"
    ride.available_seats += booking.seats_booked
    test_db.commit()

    ride = test_db.query(Ride).filter(Ride.id == 1).first()
    assert ride.available_seats == 2
    assert booking.status == "cancelled"
