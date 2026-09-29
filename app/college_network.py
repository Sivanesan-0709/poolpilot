import re
import datetime
from typing import List, Dict, Any, Optional
from app.routing import haversine_distance, search_places


VERIFIED_COLLEGE_DOMAINS = {
    "rec.ac.in": "Rajalakshmi Engineering College (REC)",
    "rajalakshmi.edu.in": "Rajalakshmi Engineering College (REC)",
    "annauniv.edu": "Anna University (CEG / ACT)",
    "iitm.ac.in": "IIT Madras",
    "srmist.edu.in": "SRM Institute of Science & Technology",
    "vit.ac.in": "VIT Chennai",
    "ssn.edu.in": "SSN College of Engineering",
    "loyola.edu.in": "Loyola College Chennai",
    "veltech.edu.in": "Vel Tech Rangarajan Dr. Sagunthala R&D Institute",
    "svce.ac.in": "Sri Venkateswara College of Engineering (SVCE)",
    "bsauniv.ac.in": "B.S. Abdur Rahman Crescent Institute",
    "sathyabama.ac.in": "Sathyabama Institute of Science and Technology"
}

COLLEGE_CAMPUSES = [
    {
        "name": "Rajalakshmi Engineering College (REC)",
        "domain": "rec.ac.in",
        "zone": "Thandalam",
        "lat": 13.0189,
        "lng": 80.0034,
        "address": "Rajalakshmi Nagar, Thandalam, Chennai 602105"
    },
    {
        "name": "Anna University (CEG Campus)",
        "domain": "annauniv.edu",
        "zone": "Guindy",
        "lat": 13.0125,
        "lng": 80.2355,
        "address": "Sardar Patel Road, Guindy, Chennai 600025"
    },
    {
        "name": "IIT Madras",
        "domain": "iitm.ac.in",
        "zone": "Adyar / Guindy",
        "lat": 12.9915,
        "lng": 80.2337,
        "address": "IIT P.O., Chennai 600036"
    },
    {
        "name": "SRM Institute of Science & Technology",
        "domain": "srmist.edu.in",
        "zone": "Kattankulathur",
        "lat": 12.8231,
        "lng": 80.0442,
        "address": "GST Road, Kattankulathur, Chennai 603203"
    },
    {
        "name": "SSN College of Engineering",
        "domain": "ssn.edu.in",
        "zone": "Kalavakkam (OMR)",
        "lat": 12.7509,
        "lng": 80.1970,
        "address": "Old Mahabalipuram Road, Kalavakkam 603110"
    }
]


def verify_college_email(email: str) -> Dict[str, Any]:
    """
    Validates student/faculty email address domain against authorized Chennai colleges.
    """
    if not email or "@" not in email:
        return {"is_valid": False, "college_name": None, "message": "Invalid email format"}

    domain = email.split("@")[1].strip().lower()
    for college_domain, college_name in VERIFIED_COLLEGE_DOMAINS.items():
        if domain == college_domain or domain.endswith(f".{college_domain}"):
            return {
                "is_valid": True,
                "domain": college_domain,
                "college_name": college_name,
                "student_discount_pct": 15,
                "message": f"Successfully verified student email for {college_name}!"
            }

    return {
        "is_valid": False,
        "college_name": None,
        "domain": domain,
        "message": f"Domain '@{domain}' is not in the recognized partner colleges list. Please upload a Student ID card for manual verification."
    }


def calculate_student_fare(base_fare: float, discount_pct: float = 15.0) -> Dict[str, float]:
    """Applies a 15% student commute subsidy/discount to the base carpool fare."""
    discount_amount = round(base_fare * (discount_pct / 100.0), 2)
    student_fare = max(15.0, round(base_fare - discount_amount, 2))
    return {
        "original_fare": base_fare,
        "discount_percent": discount_pct,
        "discount_amount": discount_amount,
        "student_fare": student_fare
    }


def cluster_student_commuters(
    student_requests: List[Dict[str, Any]],
    college_destination: str = "Rajalakshmi Engineering College (REC)",
    max_distance_km: float = 2.5,
    max_time_diff_min: int = 20
) -> List[Dict[str, Any]]:
    """
    Auto-clustering algorithm:
    Clusters students living within 2.5 km of each other with departure times within 20 mins
    heading to the same college campus.
    """
    clusters = []
    used_indices = set()

    for i, req1 in enumerate(student_requests):
        if i in used_indices:
            continue

        cluster_members = [req1]
        used_indices.add(i)

        for j, req2 in enumerate(student_requests):
            if j in used_indices:
                continue

            # Check spatial proximity
            dist = haversine_distance(
                req1["pickup_lat"], req1["pickup_lng"],
                req2["pickup_lat"], req2["pickup_lng"]
            )

            # Check time difference in minutes
            t1 = req1.get("departure_minutes", 480)
            t2 = req2.get("departure_minutes", 480)
            time_diff = abs(t1 - t2)

            if dist <= max_distance_km and time_diff <= max_time_diff_min:
                cluster_members.append(req2)
                used_indices.add(j)

        if len(cluster_members) >= 2:
            # Form a suggested cluster pool
            avg_lat = sum(m["pickup_lat"] for m in cluster_members) / len(cluster_members)
            avg_lng = sum(m["pickup_lng"] for m in cluster_members) / len(cluster_members)
            cluster_zone = cluster_members[0].get("pickup_name", "Cluster Hub")

            clusters.append({
                "cluster_id": f"clust_{len(clusters) + 1}",
                "college": college_destination,
                "zone_hub": cluster_zone,
                "center_lat": round(avg_lat, 5),
                "center_lng": round(avg_lng, 5),
                "members_count": len(cluster_members),
                "members": cluster_members,
                "suggested_departure": req1.get("departure_time", "07:45 AM"),
                "estimated_savings_per_student": round(len(cluster_members) * 35.0, 0),
                "status": "ready_to_pool"
            })

    return clusters
