import re
from typing import Dict, Any, Optional
from app.routing import search_places, load_chennai_places


def parse_voice_booking_command(voice_text: str) -> Dict[str, Any]:
    """
    Parses voice query transcript into structured booking parameters:
    - Destination (matched against Chennai gazetteer)
    - Origin (if spoken, else fallback to current location / Guindy)
    - Time (e.g. 8 AM, 8:30 AM, 16:00, 5 PM -> HH:MM format)
    - Seats needed
    """
    if not voice_text or not voice_text.strip():
        return {"success": False, "message": "No voice text provided."}

    text = voice_text.strip().lower()

    # 1. Parse Time
    dept_time = "08:30"  # default
    # Match patterns like: "8:30 am", "8 am", "5:00 pm", "5 pm", "16:30", "at 9"
    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        ampm = time_match.group(3)

        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            dept_time = f"{hour:02d}:{minute:02d}"

    # 2. Parse Seats
    seats = 1
    seat_match = re.search(r"\b(\d+)\s*(?:seat|seats|passenger|people)\b", text)
    if seat_match:
        try:
            seats = max(1, min(4, int(seat_match.group(1))))
        except Exception:
            seats = 1

    # 3. Parse Origin and Destination
    # Look for "from <origin> to <dest>" or "to <dest>" or "ride to <dest>"
    dest_str = ""
    origin_str = ""

    from_to_match = re.search(r"from\s+([a-z0-9\s]+?)\s+to\s+([a-z0-9\s]+?)(?:\s+at|\s+around|\s+for|\s+with|$)", text)
    if from_to_match:
        origin_str = from_to_match.group(1).strip()
        dest_str = from_to_match.group(2).strip()
    else:
        to_match = re.search(r"(?:to|towards|reach|drop at)\s+([a-z0-9\s]+?)(?:\s+at|\s+around|\s+for|\s+with|$)", text)
        if to_match:
            dest_str = to_match.group(1).strip()

    # Fallback to search query if no specific prefix
    if not dest_str:
        # Check against gazetteer place names
        all_places = load_chennai_places()
        for p in all_places:
            if p["name"].lower() in text or any(k in text for k in p.get("keywords", [])):
                dest_str = p["name"]
                break

    dest_results = search_places(dest_str or "Guindy", limit=1)
    drop_place = dest_results[0] if dest_results else None

    origin_place = None
    if origin_str:
        orig_results = search_places(origin_str, limit=1)
        origin_place = orig_results[0] if orig_results else None

    return {
        "success": True,
        "original_text": voice_text,
        "departure_time": dept_time,
        "seats_needed": seats,
        "drop_place": drop_place,
        "origin_place": origin_place,
        "parsed_summary": f"Pool to {drop_place['name'] if drop_place else 'destination'} at {dept_time} ({seats} seat{'s' if seats > 1 else ''})"
    }
