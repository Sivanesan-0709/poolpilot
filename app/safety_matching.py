from typing import List, Dict, Any, Optional


def check_driver_safety_criteria(
    driver: Any,
    rider: Any,
    safety_prefs: Dict[str, Any],
    pickup_name: str = "",
    drop_name: str = ""
) -> Dict[str, Any]:
    """
    Evaluates a driver against rider's safety preferences.
    Returns whether the driver passed and which preferences failed.
    """
    failures = []

    # 1. Verified ID Only
    if safety_prefs.get("verified_id_only", False):
        if not getattr(driver, "is_id_verified", False):
            failures.append("verified_id")

    # 2. Same College / Company Only
    if safety_prefs.get("same_org_only", False):
        rider_org = (getattr(rider, "college_company", "") or "").strip().lower()
        driver_org = (getattr(driver, "college_company", "") or "").strip().lower()
        if not rider_org or not driver_org or rider_org not in driver_org and driver_org not in rider_org:
            failures.append("same_org")

    # 3. Same Gender Only
    if safety_prefs.get("same_gender_only", False):
        rider_gender = (getattr(rider, "gender", "") or "other").strip().lower()
        driver_gender = (getattr(driver, "gender", "") or "other").strip().lower()
        if rider_gender != driver_gender:
            failures.append("same_gender")

    # 4. Minimum Driver Rating Slider (3.0 - 5.0)
    min_rating = safety_prefs.get("min_driver_rating")
    if min_rating is not None and float(min_rating) > 0:
        driver_rating = float(getattr(driver, "avg_rating", 5.0))
        if driver_rating < float(min_rating):
            failures.append("min_rating")

    # 5. Zero Complaints in last 30 days
    if safety_prefs.get("zero_complaints_only", False):
        complaints = int(getattr(driver, "complaints_count", 0)) + int(getattr(driver, "reports_count", 0))
        if complaints > 0:
            failures.append("zero_complaints")

    # 6. Emergency Contact On File
    if safety_prefs.get("emergency_contact_required", False):
        driver_contacts = getattr(driver, "emergency_contacts", [])
        if not driver_contacts or len(driver_contacts) == 0:
            failures.append("emergency_contact")

    # 7. Preferred Pickup/Drop Zones Only
    pref_zones = safety_prefs.get("preferred_zones", [])
    if pref_zones and len(pref_zones) > 0:
        zone_matched = any(
            z.lower() in pickup_name.lower() or z.lower() in drop_name.lower()
            for z in pref_zones
        )
        if not zone_matched:
            failures.append("preferred_zones")

    return {
        "passed": len(failures) == 0,
        "failed_criteria": failures
    }


def apply_safety_filter(
    matches: List[Dict[str, Any]],
    rider: Any,
    safety_prefs: Optional[Dict[str, Any]] = None,
    pickup_name: str = "",
    drop_name: str = ""
) -> Dict[str, Any]:
    """
    Applies the Dynamic Safety Matching Layer to a list of candidate matches.
    If 0 matches remain, generates single-click relaxation suggestions with count of added matches.
    """
    if not safety_prefs:
        return {
            "filtered_matches": matches,
            "original_count": len(matches),
            "filtered_count": len(matches),
            "rejection_reasons": {},
            "relaxation_suggestions": []
        }

    filtered_matches = []
    rejection_reasons_count = {
        "verified_id": 0,
        "same_org": 0,
        "same_gender": 0,
        "min_rating": 0,
        "zero_complaints": 0,
        "emergency_contact": 0,
        "preferred_zones": 0
    }

    match_failure_map = {}

    for m in matches:
        driver = m.get("driver")
        eval_res = check_driver_safety_criteria(
            driver=driver,
            rider=rider,
            safety_prefs=safety_prefs,
            pickup_name=pickup_name,
            drop_name=drop_name
        )
        if eval_res["passed"]:
            filtered_matches.append(m)
        else:
            match_failure_map[m["ride_id"]] = eval_res["failed_criteria"]
            for crit in eval_res["failed_criteria"]:
                if crit in rejection_reasons_count:
                    rejection_reasons_count[crit] += 1

    relaxation_suggestions = []
    # If filtered results are empty or low, suggest relaxations
    if len(filtered_matches) == 0 and len(matches) > 0:
        # Check impact of relaxing each active preference individually
        for pref_key in ["min_rating", "same_org", "verified_id", "same_gender", "zero_complaints", "emergency_contact", "preferred_zones"]:
            # If removing this single failure criterion allows matches through:
            potential_added = 0
            for r_id, fails in match_failure_map.items():
                if fails == [pref_key]:
                    potential_added += 1

            if potential_added > 0:
                if pref_key == "min_rating":
                    relaxation_suggestions.append({
                        "preference": "min_driver_rating",
                        "field": "min_driver_rating",
                        "suggested_value": 4.0,
                        "additional_matches": potential_added,
                        "message": f"Relax rating filter to 4.0★: +{potential_added} match{'es' if potential_added > 1 else ''}"
                    })
                elif pref_key == "same_org":
                    relaxation_suggestions.append({
                        "preference": "same_org_only",
                        "field": "same_org_only",
                        "suggested_value": False,
                        "additional_matches": potential_added,
                        "message": f"Include other verified colleges & workplaces: +{potential_added} match{'es' if potential_added > 1 else ''}"
                    })
                elif pref_key == "verified_id":
                    relaxation_suggestions.append({
                        "preference": "verified_id_only",
                        "field": "verified_id_only",
                        "suggested_value": False,
                        "additional_matches": potential_added,
                        "message": f"Include phone-verified community drivers: +{potential_added} match{'es' if potential_added > 1 else ''}"
                    })
                elif pref_key == "same_gender":
                    relaxation_suggestions.append({
                        "preference": "same_gender_only",
                        "field": "same_gender_only",
                        "suggested_value": False,
                        "additional_matches": potential_added,
                        "message": f"Switch to All Genders with Gold Trust: +{potential_added} match{'es' if potential_added > 1 else ''}"
                    })
                elif pref_key == "zero_complaints":
                    relaxation_suggestions.append({
                        "preference": "zero_complaints_only",
                        "field": "zero_complaints_only",
                        "suggested_value": False,
                        "additional_matches": potential_added,
                        "message": f"Include drivers with resolved feedback: +{potential_added} match{'es' if potential_added > 1 else ''}"
                    })
                elif pref_key == "emergency_contact":
                    relaxation_suggestions.append({
                        "preference": "emergency_contact_required",
                        "field": "emergency_contact_required",
                        "suggested_value": False,
                        "additional_matches": potential_added,
                        "message": f"Relax driver emergency contact requirement: +{potential_added} match{'es' if potential_added > 1 else ''}"
                    })
                elif pref_key == "preferred_zones":
                    relaxation_suggestions.append({
                        "preference": "preferred_zones",
                        "field": "preferred_zones",
                        "suggested_value": [],
                        "additional_matches": potential_added,
                        "message": f"Expand zone radius across Chennai: +{potential_added} match{'es' if potential_added > 1 else ''}"
                    })

    return {
        "filtered_matches": filtered_matches,
        "original_count": len(matches),
        "filtered_count": len(filtered_matches),
        "rejection_reasons": rejection_reasons_count,
        "relaxation_suggestions": relaxation_suggestions
    }
