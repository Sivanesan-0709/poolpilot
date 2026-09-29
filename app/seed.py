import os
import sys
import json
import datetime
import random
from app.database import Base, engine, SessionLocal
from app.models import User, DriverProfile, Ride, Booking, RideReview, SafetyEvent, HistoricalDemand, CollegePool, TripShareToken
from app.routing import get_route_geometry, search_places, haversine_distance
from app.pricing import calculate_pool_fare, calculate_auto_fare
from app.safety import calculate_trust_score


DEMO_USERS = [
    {
        "id": 1,
        "name": "Rahul Verma",
        "phone": "9840112233",
        "email": "rahul.verma@rec.ac.in",
        "role": "rider",
        "gender": "male",
        "college_company": "Rajalakshmi Engineering College (REC)",
        "is_id_verified": True,
        "is_phone_verified": True,
        "is_org_verified": True,
        "is_member": False,
        "trust_score": 85,
        "wallet_balance": 250.0,
        "referral_code": "RAHUL20",
        "total_rides": 8,
        "cancellations": 0,
        "reports_count": 0,
        "on_time_rate": 96.0,
        "completion_rate": 100.0,
        "cancellation_rate": 0.0,
        "complaints_count": 0,
        "rating_sum": 38.4,
        "rating_count": 8,
        "emergency_contacts": [
            {"name": "Suresh Verma (Father)", "phone": "9840998877", "relation": "Parent"},
            {"name": "Pooja Verma (Sister)", "phone": "9840119988", "relation": "Sibling"}
        ],
        "trusted_contacts": [
            {"name": "Suresh Verma (Father)", "phone": "9840998877", "relation": "Parent"},
            {"name": "Pooja Verma (Sister)", "phone": "9840119988", "relation": "Sibling"}
        ],
        "safety_preferences": {
            "verified_id_only": True,
            "same_org_only": False,
            "same_gender_only": False,
            "min_driver_rating": 4.0,
            "zero_complaints_only": True,
            "emergency_contact_required": False
        }
    },
    {
        "id": 2,
        "name": "Priya Sundaram",
        "phone": "9840223344",
        "email": "priya.sundaram@cognizant.com",
        "role": "rider",
        "gender": "female",
        "college_company": "Cognizant Karapakkam (OMR)",
        "is_id_verified": True,
        "is_phone_verified": True,
        "is_org_verified": True,
        "is_member": True,
        "trust_score": 92,
        "wallet_balance": 350.0,
        "referral_code": "PRIYA99",
        "total_rides": 15,
        "cancellations": 0,
        "reports_count": 0,
        "on_time_rate": 98.0,
        "completion_rate": 100.0,
        "cancellation_rate": 0.0,
        "complaints_count": 0,
        "rating_sum": 73.5,
        "rating_count": 15,
        "emergency_contacts": [
            {"name": "Meenakshi Sundaram (Mother)", "phone": "9444123456", "relation": "Mother"},
            {"name": "Deepak Raj (Spouse)", "phone": "9840332211", "relation": "Spouse"}
        ],
        "trusted_contacts": [
            {"name": "Meenakshi Sundaram (Mother)", "phone": "9444123456", "relation": "Mother"},
            {"name": "Deepak Raj (Spouse)", "phone": "9840332211", "relation": "Spouse"}
        ],
        "safety_preferences": {
            "verified_id_only": True,
            "same_org_only": False,
            "same_gender_only": True,
            "min_driver_rating": 4.5,
            "zero_complaints_only": True,
            "emergency_contact_required": True
        }
    },
    {
        "id": 3,
        "name": "Karthik Subramanian",
        "phone": "9840334455",
        "email": "karthik.subbu@tcs.com",
        "role": "driver",
        "gender": "male",
        "college_company": "TCS Siruseri (OMR)",
        "is_id_verified": True,
        "is_phone_verified": True,
        "is_org_verified": True,
        "is_member": True,
        "trust_score": 95,
        "wallet_balance": 520.0,
        "referral_code": "KARTHIK49",
        "total_rides": 24,
        "cancellations": 0,
        "reports_count": 0,
        "on_time_rate": 97.5,
        "completion_rate": 100.0,
        "cancellation_rate": 1.0,
        "complaints_count": 0,
        "rating_sum": 117.6,
        "rating_count": 24,
        "vehicle_number": "TN 09 AB 1234",
        "vehicle_model": "Honda City (White)",
        "total_seats": 4,
        "emergency_contacts": [
            {"name": "Anand Subbu (Brother)", "phone": "9884556677", "relation": "Brother"}
        ],
        "trusted_contacts": [
            {"name": "Anand Subbu (Brother)", "phone": "9884556677", "relation": "Brother"}
        ],
        "safety_preferences": {
            "verified_id_only": True,
            "min_driver_rating": 4.0
        }
    },
    {
        "id": 4,
        "name": "Ananya Krishnan",
        "phone": "9840445566",
        "email": "ananya.k@amazon.com",
        "role": "both",
        "gender": "female",
        "college_company": "Amazon Kandanchavadi",
        "is_id_verified": True,
        "is_phone_verified": True,
        "is_org_verified": True,
        "is_member": True,
        "trust_score": 88,
        "wallet_balance": 400.0,
        "referral_code": "ANANYA77",
        "total_rides": 12,
        "cancellations": 0,
        "reports_count": 0,
        "on_time_rate": 95.0,
        "completion_rate": 96.0,
        "cancellation_rate": 2.0,
        "complaints_count": 0,
        "rating_sum": 58.8,
        "rating_count": 12,
        "vehicle_number": "TN 22 C 5678",
        "vehicle_model": "Maruti Swift (Red)",
        "total_seats": 4,
        "emergency_contacts": [
            {"name": "Radha Krishnan (Mother)", "phone": "9840887766", "relation": "Mother"}
        ],
        "trusted_contacts": [
            {"name": "Radha Krishnan (Mother)", "phone": "9840887766", "relation": "Mother"}
        ],
        "safety_preferences": {
            "verified_id_only": True,
            "same_gender_only": True
        }
    },
    {
        "id": 5,
        "name": "PoolPilot Admin",
        "phone": "9999999999",
        "email": "admin@poolpilot.in",
        "role": "admin",
        "gender": "other",
        "college_company": "PoolPilot Mobility Ops",
        "is_id_verified": True,
        "is_phone_verified": True,
        "is_org_verified": True,
        "is_member": True,
        "trust_score": 100,
        "wallet_balance": 5000.0,
        "referral_code": "ADMIN01",
        "total_rides": 50,
        "cancellations": 0,
        "reports_count": 0,
        "on_time_rate": 100.0,
        "completion_rate": 100.0,
        "cancellation_rate": 0.0,
        "complaints_count": 0,
        "rating_sum": 250.0,
        "rating_count": 50,
        "emergency_contacts": [],
        "trusted_contacts": [],
        "safety_preferences": {}
    }
]

ADDITIONAL_USERS = [
    {"name": "Venkatesh Raman", "phone": "9840500001", "role": "driver", "gender": "male", "college_company": "Infosys Sholinganallur", "vehicle": ("TN 14 D 9081", "Hyundai i20 (Silver)", 4), "trust": 85, "verified": True, "on_time": 94.0, "comp": 98.0, "canc": 1.5, "complaints": 0},
    {"name": "Sneha Parthasarathy", "phone": "9840500002", "role": "both", "gender": "female", "college_company": "Wipro Technologies", "vehicle": ("TN 07 BE 4321", "Tata Nexon EV (Teal)", 4), "trust": 90, "verified": True, "on_time": 97.0, "comp": 99.0, "canc": 0.5, "complaints": 0},
    {"name": "Aravind Chandran", "phone": "9840500003", "role": "driver", "gender": "male", "college_company": "Rajalakshmi Engineering College (REC)", "vehicle": ("TN 20 AX 7890", "Toyota Glanza (Grey)", 4), "trust": 82, "verified": True, "on_time": 95.0, "comp": 98.0, "canc": 2.0, "complaints": 0},
    {"name": "Divya Nambiar", "phone": "9840500004", "role": "rider", "gender": "female", "college_company": "Anna University (CEG)", "trust": 78, "verified": True, "on_time": 92.0, "comp": 95.0, "canc": 3.0, "complaints": 0},
    {"name": "Gokul Prasad", "phone": "9840500005", "role": "driver", "gender": "male", "college_company": "DLF Cybercity", "vehicle": ("TN 10 CC 3344", "Maruti Baleno (Blue)", 4), "trust": 82, "verified": True, "on_time": 96.0, "comp": 97.0, "canc": 2.0, "complaints": 0},
    {"name": "Harini Balaji", "phone": "9840500006", "role": "rider", "gender": "female", "college_company": "IIT Madras", "trust": 86, "verified": True, "on_time": 96.5, "comp": 99.0, "canc": 1.0, "complaints": 0},
    {"name": "Manojkumar S", "phone": "9840500007", "role": "both", "gender": "male", "college_company": "HCL Technologies", "vehicle": ("TN 09 BH 1122", "Honda Amaze (White)", 4), "trust": 79, "verified": True, "on_time": 93.0, "comp": 96.0, "canc": 2.5, "complaints": 0},
    {"name": "Kavitha R", "phone": "9840500008", "role": "driver", "gender": "female", "college_company": "Standard Chartered GBS", "vehicle": ("TN 02 AN 9988", "Kia Sonet (Grey)", 4), "trust": 89, "verified": True, "on_time": 98.0, "comp": 100.0, "canc": 0.0, "complaints": 0},
    {"name": "Siddharth Menon", "phone": "9840500009", "role": "rider", "gender": "male", "college_company": "SRM University KTR", "trust": 65, "verified": True, "on_time": 88.0, "comp": 90.0, "canc": 5.0, "complaints": 0},
    {"name": "Lavanya Murali", "phone": "9840500010", "role": "rider", "gender": "female", "college_company": "PayPal Sholinganallur", "trust": 88, "verified": True, "on_time": 96.0, "comp": 99.0, "canc": 1.0, "complaints": 0},
    {"name": "Dinesh Kumar", "phone": "9840500011", "role": "driver", "gender": "male", "college_company": "Hyundai Sriperumbudur", "vehicle": ("TN 21 M 4455", "Hyundai Verna (Black)", 4), "trust": 84, "verified": True, "on_time": 94.0, "comp": 97.0, "canc": 2.0, "complaints": 0},
    {"name": "Pooja Hegde", "phone": "9840500012", "role": "rider", "gender": "female", "college_company": "Tidel Park IT Hub", "trust": 72, "verified": False, "on_time": 90.0, "comp": 92.0, "canc": 4.0, "complaints": 0},
    {"name": "Saravanan V", "phone": "9840500013", "role": "driver", "gender": "male", "college_company": "Ford Global Technology", "vehicle": ("TN 11 P 6677", "Ford EcoSport (White)", 4), "trust": 87, "verified": True, "on_time": 96.0, "comp": 98.0, "canc": 1.0, "complaints": 0},
    {"name": "Deepa Sundar", "phone": "9840500014", "role": "both", "gender": "female", "college_company": "Caterpillar India", "vehicle": ("TN 05 AF 3412", "Maruti Brezza (Red)", 4), "trust": 83, "verified": True, "on_time": 95.0, "comp": 98.0, "canc": 1.5, "complaints": 0},
    {"name": "Ashwin Raj", "phone": "9840500015", "role": "rider", "gender": "male", "college_company": "Rajalakshmi Engineering College (REC)", "trust": 70, "verified": True, "on_time": 91.0, "comp": 94.0, "canc": 3.0, "complaints": 0},
    {"name": "Gayathri Shankaran", "phone": "9840500016", "role": "rider", "gender": "female", "college_company": "Balfour Beatty OMR", "trust": 75, "verified": True, "on_time": 93.0, "comp": 96.0, "canc": 2.0, "complaints": 0},
    {"name": "Praveen Natarajan", "phone": "9840500017", "role": "driver", "gender": "male", "college_company": "L&T Construction Manapakkam", "vehicle": ("TN 09 DE 8821", "Skoda Kushaq (Silver)", 4), "trust": 91, "verified": True, "on_time": 97.0, "comp": 99.0, "canc": 1.0, "complaints": 0},
    {"name": "Nithya Ramaswamy", "phone": "9840500018", "role": "driver", "gender": "female", "college_company": "Cognizant TCO OMR", "vehicle": ("TN 07 BT 5566", "Tata Tiago EV (White)", 4), "trust": 86, "verified": True, "on_time": 96.0, "comp": 98.0, "canc": 1.0, "complaints": 0},
    {"name": "Vigneshwaran K", "phone": "9840500019", "role": "rider", "gender": "male", "college_company": "Loyola College / Nungambakkam", "trust": 68, "verified": True, "on_time": 90.0, "comp": 93.0, "canc": 4.0, "complaints": 0},
    {"name": "Archana Swaminathan", "phone": "9840500020", "role": "rider", "gender": "female", "college_company": "World Bank Chennai", "trust": 94, "verified": True, "on_time": 98.0, "comp": 100.0, "canc": 0.5, "complaints": 0}
]

DRIVER_ROUTES_DEF = [
    {
        "driver_id": 3,
        "origin": "Siruseri SIPCOT IT Park",
        "origin_lat": 12.8288,
        "origin_lng": 80.2184,
        "dest": "Perungudi Toll Gate (OMR)",
        "dest_lat": 12.9654,
        "dest_lng": 80.2461,
        "dept_time": "08:30",
        "seats": 3,
        "price_per_km": 5.5,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 4,
        "origin": "Thiruvanmiyur Beach & Bus Depot",
        "origin_lat": 12.9830,
        "origin_lng": 80.2594,
        "dest": "Siruseri SIPCOT IT Park",
        "dest_lat": 12.8288,
        "dest_lng": 80.2184,
        "dept_time": "09:00",
        "seats": 3,
        "price_per_km": 6.0,
        "women_only": True,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 6,
        "origin": "Tambaram Railway Station & Bus Stand",
        "origin_lat": 12.9249,
        "origin_lng": 80.1197,
        "dest": "T. Nagar Panagal Park / Usman Road",
        "dest_lat": 13.0418,
        "dest_lng": 80.2341,
        "dept_time": "08:45",
        "seats": 3,
        "price_per_km": 5.0,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 7,
        "origin": "Velachery Vijayanagar / Phoenix Marketcity",
        "origin_lat": 12.9759,
        "origin_lng": 80.2212,
        "dest": "Guindy Kathipara Junction & Metro",
        "dest_lat": 13.0067,
        "dest_lng": 80.2025,
        "dept_time": "09:15",
        "seats": 3,
        "price_per_km": 6.0,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 8,
        "origin": "Rajalakshmi Engineering College (REC), Thandalam",
        "origin_lat": 13.0189,
        "origin_lng": 80.0034,
        "dest": "Guindy Kathipara Junction & Metro",
        "dest_lat": 13.0067,
        "dest_lng": 80.2025,
        "dept_time": "16:30",
        "seats": 3,
        "price_per_km": 5.0,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 10,
        "origin": "Porur Junction / Ramachandra Hospital",
        "origin_lat": 13.0382,
        "origin_lng": 80.1565,
        "dest": "DLF Cybercity, Manapakkam",
        "dest_lat": 13.0215,
        "dest_lng": 80.1764,
        "dept_time": "08:50",
        "seats": 2,
        "price_per_km": 5.5,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 13,
        "origin": "Anna Nagar Roundtana / Tower Park",
        "origin_lat": 13.0850,
        "origin_lng": 80.2101,
        "dest": "Adyar Depot / Kasturba Nagar",
        "dest_lat": 13.0012,
        "dest_lng": 80.2565,
        "dept_time": "08:40",
        "seats": 3,
        "price_per_km": 6.0,
        "women_only": True,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 16,
        "origin": "Sriperumbudur Industrial Hub",
        "origin_lat": 12.9691,
        "origin_lng": 79.9406,
        "dest": "Koyambedu CMBT / Metro Hub",
        "dest_lat": 13.0694,
        "dest_lng": 80.1948,
        "dept_time": "17:30",
        "seats": 3,
        "price_per_km": 4.8,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 18,
        "origin": "Chromepet (MIT / GST Road)",
        "origin_lat": 12.9516,
        "origin_lng": 80.1462,
        "dest": "Tidel Park / Thiruvanmiyur MRTS",
        "dest_lat": 12.9897,
        "dest_lng": 80.2494,
        "dept_time": "08:15",
        "seats": 3,
        "price_per_km": 5.5,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 19,
        "origin": "Medavakkam Koot Road",
        "origin_lat": 12.9202,
        "origin_lng": 80.1884,
        "dest": "Sholinganallur Junction (ELCOT SEZ)",
        "dest_lat": 12.9010,
        "dest_lng": 80.2279,
        "dept_time": "09:05",
        "seats": 3,
        "price_per_km": 6.0,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 22,
        "origin": "Vandalur Zoo / Crescent University",
        "origin_lat": 12.8906,
        "origin_lng": 80.0811,
        "dest": "Chennai Central (Puratchi Thalaivar Dr. MGR Station)",
        "dest_lat": 13.0827,
        "dest_lng": 80.2755,
        "dept_time": "08:00",
        "seats": 3,
        "price_per_km": 5.0,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    },
    {
        "driver_id": 23,
        "origin": "Mylapore Luz Corner / Kapaleeshwarar",
        "origin_lat": 13.0368,
        "origin_lng": 80.2676,
        "dest": "Chennai International Airport (Meenambakkam)",
        "dest_lat": 12.9941,
        "dest_lng": 80.1709,
        "dept_time": "18:00",
        "seats": 3,
        "price_per_km": 6.0,
        "women_only": False,
        "recurring": ["Mon", "Tue", "Wed", "Thu", "Fri"]
    }
]

COLLEGE_POOLS_SEED = [
    # 5 Rajalakshmi Engineering College (REC) Pools
    {
        "name": "Tambaram to REC Morning Express",
        "college_name": "Rajalakshmi Engineering College (REC)",
        "college_domain": "rec.ac.in",
        "origin_zone": "Tambaram Railway Station",
        "destination_zone": "Rajalakshmi Engineering College (REC), Thandalam",
        "origin_lat": 12.9249,
        "origin_lng": 80.1197,
        "destination_lat": 13.0189,
        "destination_lng": 80.0034,
        "departure_time": "07:45 AM",
        "time_window": "7:30 - 8:00 AM",
        "direction": "home_to_college",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "host_user_id": 8,  # Aravind Chandran
        "member_ids": [1, 15],  # Rahul Verma, Ashwin Raj
        "total_seats": 4,
        "available_seats": 2,
        "fare_per_seat": 45.0,
        "original_fare": 55.0,
        "notices": [
            {"id": 1, "author": "Aravind Chandran (Host)", "text": "Pickup point near Tambaram West Bus Stand entrance at 7:45 AM sharp.", "time": "Yesterday"},
            {"id": 2, "author": "Rahul Verma", "text": "Will be there near the ticket counter by 7:40 AM.", "time": "Yesterday"}
        ]
    },
    {
        "name": "Velachery to REC Tech Commute",
        "college_name": "Rajalakshmi Engineering College (REC)",
        "college_domain": "rec.ac.in",
        "origin_zone": "Velachery Vijayanagar",
        "destination_zone": "Rajalakshmi Engineering College (REC), Thandalam",
        "origin_lat": 12.9759,
        "origin_lng": 80.2212,
        "destination_lat": 13.0189,
        "destination_lng": 80.0034,
        "departure_time": "07:30 AM",
        "time_window": "7:15 - 7:45 AM",
        "direction": "home_to_college",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "host_user_id": 8,
        "member_ids": [15],
        "total_seats": 4,
        "available_seats": 3,
        "fare_per_seat": 50.0,
        "original_fare": 60.0,
        "notices": [
            {"id": 1, "author": "Aravind Chandran (Host)", "text": "Starting from Velachery MRTS station via Porur bypass.", "time": "2 days ago"}
        ]
    },
    {
        "name": "Porur to REC Quick Ride",
        "college_name": "Rajalakshmi Engineering College (REC)",
        "college_domain": "rec.ac.in",
        "origin_zone": "Porur Roundtana",
        "destination_zone": "Rajalakshmi Engineering College (REC), Thandalam",
        "origin_lat": 13.0382,
        "origin_lng": 80.1565,
        "destination_lat": 13.0189,
        "destination_lng": 80.0034,
        "departure_time": "08:00 AM",
        "time_window": "7:45 - 8:15 AM",
        "direction": "home_to_college",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "host_user_id": 10,
        "member_ids": [1],
        "total_seats": 4,
        "available_seats": 3,
        "fare_per_seat": 35.0,
        "original_fare": 42.0,
        "notices": [
            {"id": 1, "author": "Gokul Prasad", "text": "Departs Porur toll gate at 8:00 AM. Fast route on NH48.", "time": "3 days ago"}
        ]
    },
    {
        "name": "Anna Nagar to REC Western Line",
        "college_name": "Rajalakshmi Engineering College (REC)",
        "college_domain": "rec.ac.in",
        "origin_zone": "Anna Nagar Roundtana",
        "destination_zone": "Rajalakshmi Engineering College (REC), Thandalam",
        "origin_lat": 13.0850,
        "origin_lng": 80.2101,
        "destination_lat": 13.0189,
        "destination_lng": 80.0034,
        "departure_time": "07:35 AM",
        "time_window": "7:20 - 7:50 AM",
        "direction": "home_to_college",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "host_user_id": 13,
        "member_ids": [15],
        "total_seats": 4,
        "available_seats": 2,
        "fare_per_seat": 55.0,
        "original_fare": 65.0,
        "notices": [
            {"id": 1, "author": "Kavitha R (Host)", "text": "AC hatchback, non-smoking, women/student friendly pool.", "time": "1 day ago"}
        ]
    },
    {
        "name": "REC to Guindy Evening Return",
        "college_name": "Rajalakshmi Engineering College (REC)",
        "college_domain": "rec.ac.in",
        "origin_zone": "Rajalakshmi Engineering College (REC), Thandalam",
        "destination_zone": "Guindy Kathipara Junction & Metro",
        "origin_lat": 13.0189,
        "origin_lng": 80.0034,
        "destination_lat": 13.0067,
        "destination_lng": 80.2025,
        "departure_time": "04:30 PM",
        "time_window": "4:15 - 4:45 PM",
        "direction": "college_to_home",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "host_user_id": 8,
        "member_ids": [1, 15],
        "total_seats": 4,
        "available_seats": 2,
        "fare_per_seat": 45.0,
        "original_fare": 55.0,
        "notices": [
            {"id": 1, "author": "Aravind Chandran (Host)", "text": "Assemble at REC Main Gate parking at 4:25 PM.", "time": "Yesterday"}
        ]
    },

    # 2 Anna University Pools
    {
        "name": "Tambaram to Anna University Main Gate",
        "college_name": "Anna University (CEG / ACT)",
        "college_domain": "annauniv.edu",
        "origin_zone": "Tambaram Railway Station",
        "destination_zone": "Anna University Guindy Campus",
        "origin_lat": 12.9249,
        "origin_lng": 80.1197,
        "destination_lat": 13.0125,
        "destination_lng": 80.2355,
        "departure_time": "08:15 AM",
        "time_window": "8:00 - 8:30 AM",
        "direction": "home_to_college",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "host_user_id": 6,
        "member_ids": [4],
        "total_seats": 4,
        "available_seats": 2,
        "fare_per_seat": 40.0,
        "original_fare": 48.0,
        "notices": [
            {"id": 1, "author": "Venkatesh Raman (Host)", "text": "Direct via GST road to Sardar Patel Road gate.", "time": "2 days ago"}
        ]
    },
    {
        "name": "Anna Nagar to Anna University Morning Pool",
        "college_name": "Anna University (CEG / ACT)",
        "college_domain": "annauniv.edu",
        "origin_zone": "Anna Nagar Tower",
        "destination_zone": "Anna University Guindy Campus",
        "origin_lat": 13.0850,
        "origin_lng": 80.2101,
        "destination_lat": 13.0125,
        "destination_lng": 80.2355,
        "departure_time": "08:20 AM",
        "time_window": "8:05 - 8:35 AM",
        "direction": "home_to_college",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "host_user_id": 13,
        "member_ids": [4],
        "total_seats": 4,
        "available_seats": 2,
        "fare_per_seat": 35.0,
        "original_fare": 42.0,
        "notices": [
            {"id": 1, "author": "Kavitha R (Host)", "text": "Departing from Tower park gate. Drop at CEG Kotturpuram gate.", "time": "1 day ago"}
        ]
    }
]


def seed_database(reset: bool = False):
    """Seed the database with users, drivers, routes, college pools, historical demand, and reviews."""
    if reset:
        print("[Seed] Resetting database tables...")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing_users = db.query(User).count()
        if existing_users >= 20 and not reset:
            print(f"[Seed] Database already contains {existing_users} users. Skipping seed.")
            return

        print("[Seed] Creating demo accounts and community users...")

        # 1. Seed Demo Users
        for u in DEMO_USERS:
            user = User(
                id=u["id"],
                name=u["name"],
                phone=u["phone"],
                email=u["email"],
                role=u["role"],
                gender=u["gender"],
                college_company=u["college_company"],
                is_id_verified=u["is_id_verified"],
                id_doc_filename="aadhaar_mock_verified.png",
                selfie_filename="selfie_mock_verified.png",
                is_phone_verified=u["is_phone_verified"],
                is_org_verified=u["is_org_verified"],
                is_member=u["is_member"],
                trust_score=u["trust_score"],
                wallet_balance=u["wallet_balance"],
                referral_code=u["referral_code"],
                total_rides=u["total_rides"],
                cancellations=u["cancellations"],
                reports_count=u["reports_count"],
                on_time_rate=u.get("on_time_rate", 95.0),
                completion_rate=u.get("completion_rate", 98.0),
                cancellation_rate=u.get("cancellation_rate", 2.0),
                complaints_count=u.get("complaints_count", 0),
                rating_sum=u["rating_sum"],
                rating_count=u["rating_count"]
            )
            user.emergency_contacts = u.get("emergency_contacts", [])
            user.trusted_contacts = u.get("trusted_contacts", [])
            user.safety_preferences = u.get("safety_preferences", {})
            db.add(user)
            db.flush()

            if "vehicle_number" in u:
                profile = DriverProfile(
                    user_id=user.id,
                    vehicle_number=u["vehicle_number"],
                    vehicle_model=u["vehicle_model"],
                    total_seats=u.get("total_seats", 4),
                    license_number=f"DL-TN-{user.id:04d}",
                    is_verified_driver=True
                )
                db.add(profile)

        # 2. Seed Additional Commuters
        curr_id = 6
        for extra in ADDITIONAL_USERS:
            user = User(
                id=curr_id,
                name=extra["name"],
                phone=extra["phone"],
                email=f"{extra['name'].lower().replace(' ', '.')}@gmail.com",
                role=extra["role"],
                gender=extra["gender"],
                college_company=extra.get("college_company"),
                is_id_verified=extra.get("verified", True),
                id_doc_filename="gov_id_sample.png",
                selfie_filename="user_selfie.png",
                is_phone_verified=True,
                is_org_verified=extra.get("verified", True),
                is_member=(curr_id % 3 == 0),
                trust_score=extra.get("trust", 75),
                wallet_balance=random.choice([150.0, 250.0, 350.0]),
                referral_code=f"POOL{curr_id:03d}",
                total_rides=random.randint(4, 18),
                cancellations=random.randint(0, 1),
                reports_count=0,
                on_time_rate=extra.get("on_time", 95.0),
                completion_rate=extra.get("comp", 98.0),
                cancellation_rate=extra.get("canc", 2.0),
                complaints_count=extra.get("complaints", 0),
                rating_sum=random.randint(4, 18) * 4.8,
                rating_count=random.randint(4, 18)
            )
            user.emergency_contacts = [
                {"name": "Home Emergency", "phone": "9840000000", "relation": "Family"}
            ]
            user.trusted_contacts = [
                {"name": "Home Emergency", "phone": "9840000000", "relation": "Family"}
            ]
            db.add(user)
            db.flush()

            if "vehicle" in extra:
                v_num, v_model, v_seats = extra["vehicle"]
                profile = DriverProfile(
                    user_id=user.id,
                    vehicle_number=v_num,
                    vehicle_model=v_model,
                    total_seats=v_seats,
                    license_number=f"DL-TN-{curr_id:04d}",
                    is_verified_driver=True
                )
                db.add(profile)

            curr_id += 1

        db.commit()
        print(f"[Seed] Successfully seeded {curr_id - 1} users and driver profiles.")

        # 3. Seed Realistic Driver Routes with Precomputed Polylines
        print("[Seed] Precomputing and storing realistic driver routes across Chennai corridors...")
        today_str = datetime.date.today().isoformat()

        for idx, r_def in enumerate(DRIVER_ROUTES_DEF, start=1):
            route_info = get_route_geometry(
                r_def["origin_lat"], r_def["origin_lng"],
                r_def["dest_lat"], r_def["dest_lng"]
            )

            dept_iso = f"{today_str}T{r_def['dept_time']}"
            ride = Ride(
                id=idx,
                driver_id=r_def["driver_id"],
                origin_name=r_def["origin"],
                origin_lat=r_def["origin_lat"],
                origin_lng=r_def["origin_lng"],
                destination_name=r_def["dest"],
                destination_lat=r_def["dest_lat"],
                destination_lng=r_def["dest_lng"],
                departure_time=dept_iso,
                available_seats=r_def["seats"],
                total_seats=4,
                price_per_km=r_def["price_per_km"],
                is_women_only=r_def["women_only"],
                route_distance_km=route_info["distance_km"],
                route_duration_min=route_info["duration_min"],
                status="open",
                is_offline_routing=route_info.get("is_offline", False)
            )
            ride.route_polyline = route_info["polyline"]
            ride.recurring_days = r_def.get("recurring", [])
            db.add(ride)

        db.commit()
        print("[Seed] Seeded 12 active driver routes.")

        # 4. Seed College Pools (5 REC + 2 Anna University)
        print("[Seed] Seeding 7 student commute pools for REC and Anna University...")
        for p_idx, pool_data in enumerate(COLLEGE_POOLS_SEED, start=1):
            cp = CollegePool(
                id=p_idx,
                name=pool_data["name"],
                college_name=pool_data["college_name"],
                college_domain=pool_data["college_domain"],
                origin_zone=pool_data["origin_zone"],
                destination_zone=pool_data["destination_zone"],
                origin_lat=pool_data["origin_lat"],
                origin_lng=pool_data["origin_lng"],
                destination_lat=pool_data["destination_lat"],
                destination_lng=pool_data["destination_lng"],
                departure_time=pool_data["departure_time"],
                time_window=pool_data["time_window"],
                direction=pool_data["direction"],
                host_user_id=pool_data["host_user_id"],
                total_seats=pool_data["total_seats"],
                available_seats=pool_data["available_seats"],
                fare_per_seat=pool_data["fare_per_seat"],
                original_fare=pool_data["original_fare"],
                status="active"
            )
            cp.days = pool_data["days"]
            cp.member_ids = pool_data["member_ids"]
            cp.notices = pool_data["notices"]
            db.add(cp)

        db.commit()
        print("[Seed] Seeded 7 college pools.")

        # 5. Seed Historical Demand data points for heatmaps & ML demand prediction
        print("[Seed] Generating 40 historical demand points across Chennai rush hours...")
        hotspot_zones = [
            ("Siruseri SIPCOT IT Park", 12.8288, 80.2184, [8, 9, 17, 18, 19]),
            ("Perungudi OMR Toll", 12.9654, 80.2461, [8, 9, 10, 18, 19, 20]),
            ("Sholinganallur ELCOT", 12.9010, 80.2279, [8, 9, 18, 19]),
            ("Guindy Kathipara Hub", 13.0067, 80.2025, [8, 9, 10, 17, 18, 19]),
            ("Tambaram Railway Hub", 12.9249, 80.1197, [7, 8, 9, 17, 18]),
            ("REC Thandalam", 13.0189, 80.0034, [8, 9, 16, 17]),
            ("Velachery Vijayanagar", 12.9759, 80.2212, [8, 9, 18, 19, 20]),
            ("T. Nagar Panagal Park", 13.0418, 80.2341, [10, 11, 16, 17, 18, 19]),
            ("Porur Junction / DLF", 13.0382, 80.1565, [8, 9, 18, 19]),
            ("Anna Nagar Roundtana", 13.0850, 80.2101, [8, 9, 18, 19])
        ]

        count = 0
        for zone_name, z_lat, z_lng, hours in hotspot_zones:
            for hr in hours:
                hd = HistoricalDemand(
                    zone_name=zone_name,
                    lat=round(z_lat + random.uniform(-0.005, 0.005), 5),
                    lng=round(z_lng + random.uniform(-0.005, 0.005), 5),
                    hour_of_day=hr,
                    day_of_week=random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
                    request_count=random.randint(3, 14),
                    density=round(random.uniform(0.6, 1.0), 2)
                )
                db.add(hd)
                count += 1

        db.commit()
        print(f"[Seed] Seeded {count} historical demand records.")

        # 6. Seed Reviews for Learned Preference Boost
        print("[Seed] Seeding completed ride reviews for user preference learning...")
        reviews = [
            RideReview(ride_id=1, from_user_id=1, to_user_id=3, rating=5.0, comment="Great punctuality and safe driving! Highly recommended pool.", is_anonymous=False),
            RideReview(ride_id=1, from_user_id=2, to_user_id=3, rating=5.0, comment="Clean car, comfortable AC commute along OMR.", is_anonymous=False),
            RideReview(ride_id=2, from_user_id=2, to_user_id=4, rating=5.0, comment="Loved the women-only pool! Felt super safe and convenient.", is_anonymous=False),
            RideReview(ride_id=5, from_user_id=1, to_user_id=8, rating=4.8, comment="Daily college ride from REC to Guindy saved me hours of MTC bus transit!", is_anonymous=False)
        ]
        db.add_all(reviews)
        db.commit()

        print("[Seed] Seed data generation complete and verified!")

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error during seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    is_reset = "--reset" in sys.argv
    seed_database(reset=is_reset)
