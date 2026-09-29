import pytest
from app.config import AI_CONFIG
from app.ai_forecasting import predict_zone_demand
from app.ai_voice import parse_voice_booking_command
from app.ai_ocr import extract_vehicle_plate_ocr
from app.ai_facematch import verify_face_match
from app.ai_semantic import semantic_place_search


def test_demand_forecasting_fallback():
    # Test morning rush hour prediction
    res_morning = predict_zone_demand("OMR Expressway (Siruseri to Sholinganallur)", target_hour=9)
    assert "predicted_riders" in res_morning
    assert res_morning["predicted_riders"] >= 3
    assert "model_used" in res_morning
    assert "confidence_range" in res_morning
    assert len(res_morning["confidence_range"]) == 2
    assert res_morning["confidence_range"][0] <= res_morning["confidence_range"][1]

    # Test night hour prediction
    res_night = predict_zone_demand("Chennai Airport", target_hour=2)
    assert res_night["predicted_riders"] >= 1


def test_voice_booking_parser():
    # 1. Spoken destination and time: "ride to T Nagar at 8 AM"
    res1 = parse_voice_booking_command("ride to T Nagar at 8 AM")
    assert res1["success"] is True
    assert res1["departure_time"] == "08:00"
    assert res1["drop_place"] is not None
    assert "T. Nagar" in res1["drop_place"]["name"]

    # 2. Spoken from and to: "Pool from Tambaram to Guindy at 8:30 AM with 2 seats"
    res2 = parse_voice_booking_command("Pool from Tambaram to Guindy at 8:30 AM with 2 seats")
    assert res2["success"] is True
    assert res2["departure_time"] == "08:30"
    assert res2["seats_needed"] == 2
    assert res2["origin_place"] is not None
    assert "Tambaram" in res2["origin_place"]["name"]
    assert res2["drop_place"] is not None
    assert "Guindy" in res2["drop_place"]["name"]

    # 3. Spoken college commute: "Go to Rajalakshmi Engineering College REC at 4 PM"
    res3 = parse_voice_booking_command("Go to Rajalakshmi Engineering College REC at 4 PM")
    assert res3["success"] is True
    assert res3["departure_time"] == "16:00"
    assert "Rajalakshmi" in res3["drop_place"]["name"]


def test_ocr_plate_fallback():
    # Valid Indian plate text
    res = extract_vehicle_plate_ocr(image_path_or_bytes="sample_photo.jpg", expected_plate="TN 09 AB 1234")
    assert res["success"] is True
    assert res["is_valid_format"] is True
    assert res["matches_registered"] is True
    assert res["confidence"] >= 0.70
    assert "model_used" in res


def test_face_match_fallback():
    res = verify_face_match("aadhaar_rahul.png", "selfie_rahul.png")
    assert res["success"] is True
    assert res["is_matched"] is True
    assert res["similarity_score"] >= 0.75
    assert res["match_percentage"] >= 75
    assert "model_used" in res


def test_semantic_search_fallback():
    # Query: "IT park near OMR"
    res = semantic_place_search("IT park near OMR", limit=5)
    assert res["count"] > 0
    top_names = [p["name"] for p in res["results"]]
    # Should rank OMR IT parks (Siruseri / Perungudi / Sholinganallur / Tidel Park) highly
    assert any("OMR" in name or "Siruseri" in name or "Perungudi" in name or "Tidel" in name or "Sholinganallur" in name for name in top_names)


def test_feature_flags_toggle():
    # Verify toggling feature flags behaves predictably
    orig_flag = AI_CONFIG.get("ENABLE_CHRONOS_DEMAND", True)
    AI_CONFIG["ENABLE_CHRONOS_DEMAND"] = False

    res = predict_zone_demand("Tambaram GST Road", target_hour=8)
    assert res["is_fallback"] is True
    assert "Fallback" in res["model_used"]

    # Restore flag
    AI_CONFIG["ENABLE_CHRONOS_DEMAND"] = orig_flag
