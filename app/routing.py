import math
import json
import os
import re
import time
import urllib.request
import urllib.parse
from typing import List, Tuple, Dict, Any, Optional

PLACES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chennai_places.json")
_LOCAL_PLACES_CACHE = None


def load_chennai_places() -> List[Dict[str, Any]]:
    global _LOCAL_PLACES_CACHE
    if _LOCAL_PLACES_CACHE is not None:
        return _LOCAL_PLACES_CACHE
    try:
        if os.path.exists(PLACES_FILE):
            with open(PLACES_FILE, "r", encoding="utf-8") as f:
                _LOCAL_PLACES_CACHE = json.load(f)
                return _LOCAL_PLACES_CACHE
    except Exception as e:
        print(f"[Routing] Warning loading places JSON: {e}")
    _LOCAL_PLACES_CACHE = []
    return _LOCAL_PLACES_CACHE


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def generate_fallback_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> Dict[str, Any]:
    """Fallback offline route calculation using Haversine x 1.3 road factor and linear interpolation."""
    air_dist = haversine_distance(start_lat, start_lng, end_lat, end_lng)
    road_dist = round(max(0.5, air_dist * 1.3), 2)  # 1.3 road winding factor
    # Average urban Chennai speed ~ 25 km/h
    duration_min = round(max(2.0, (road_dist / 25.0) * 60.0), 1)

    # Generate 15 interpolated steps for a smooth polyline
    steps = 15
    polyline = []
    for i in range(steps + 1):
        t = i / float(steps)
        lat = start_lat + (end_lat - start_lat) * t
        lng = start_lng + (end_lng - start_lng) * t
        polyline.append([round(lat, 6), round(lng, 6)])

    return {
        "polyline": polyline,
        "distance_km": road_dist,
        "duration_min": duration_min,
        "is_offline": True,
        "mode": "offline_haversine_fallback"
    }


def get_route_geometry(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> Dict[str, Any]:
    """Fetch real driving route from public OSRM, with strict 3.0s timeout and instant fallback."""
    url = f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PoolPilot/1.0 (Chennai Urban Mobility Project; academic demo)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    # GeoJSON is [lng, lat] -> convert to [lat, lng]
                    coords = [[round(pt[1], 6), round(pt[0], 6)] for pt in route["geometry"]["coordinates"]]
                    dist_km = round(route["distance"] / 1000.0, 2)
                    dur_min = round(route["duration"] / 60.0, 1)
                    return {
                        "polyline": coords,
                        "distance_km": dist_km,
                        "duration_min": dur_min,
                        "is_offline": False,
                        "mode": "osrm_online"
                    }
    except Exception as e:
        print(f"[Routing] OSRM query failed/timed out ({e}). Using offline fallback.")

    return generate_fallback_route(start_lat, start_lng, end_lat, end_lng)


def search_places(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Search built-in Chennai gazetteer first, then optional Nominatim fallback."""
    if not query or not query.strip():
        return load_chennai_places()[:limit]

    q = query.strip().lower()
    places = load_chennai_places()
    results = []

    # Local matching with ranking:
    # 1. Exact or prefix match on name (100 pts)
    # 2. Substring match on name (70 pts)
    # 3. Match in keywords/aliases (50 pts)
    # 4. Match in zone/category (30 pts)
    clean_q = re.sub(r"[^\w\s]", "", q)
    scored = []
    for p in places:
        name_lower = p["name"].lower()
        clean_name = re.sub(r"[^\w\s]", "", name_lower)
        score = 0

        if clean_name.startswith(clean_q) or name_lower.startswith(q):
            score = 100
        elif clean_q in clean_name or q in name_lower:
            score = 70
        elif any(clean_q in re.sub(r"[^\w\s]", "", kw.lower()) for kw in p.get("keywords", [])):
            score = 50
        elif clean_q in p.get("zone", "").lower() or clean_q in p.get("category", "").lower():
            score = 30

        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored[:limit]]

    if len(results) >= 3:
        return results

    # Optional Nominatim fallback if local search produced few results
    try:
        encoded_q = urllib.parse.quote(f"{query}, Chennai, Tamil Nadu")
        nom_url = f"https://nominatim.openstreetmap.org/search?q={encoded_q}&format=json&viewbox=79.8,13.2,80.4,12.7&bounded=0&limit=4"
        req = urllib.request.Request(
            nom_url,
            headers={"User-Agent": "PoolPilot/1.0 (Urban Mobility Demo)"}
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                nom_data = json.loads(resp.read().decode("utf-8"))
                for item in nom_data:
                    display_name = item.get("display_name", "")
                    lat = float(item.get("lat", 0))
                    lng = float(item.get("lon", 0))
                    if lat and lng and not any(r["name"] == display_name for r in results):
                        results.append({
                            "id": f"nom_{int(time.time()*1000)}",
                            "name": display_name.split(",")[0] + " (Chennai)",
                            "lat": round(lat, 5),
                            "lng": round(lng, 5),
                            "category": "address",
                            "zone": "Chennai",
                            "keywords": []
                        })
    except Exception:
        pass  # Never block on Nominatim

    return results[:limit] if results else load_chennai_places()[:limit]


def _project_point_to_segment(p_lat: float, p_lng: float, a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> Tuple[float, float, float]:
    """Projects point P onto line segment AB. Returns (projected_lat, projected_lng, t_ratio)."""
    # Flat approximation for short distances within city limits
    cos_lat = math.cos(math.radians((a_lat + b_lat) / 2.0))
    dx = (b_lng - a_lng) * cos_lat
    dy = b_lat - a_lat
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq < 1e-12:
        return a_lat, a_lng, 0.0

    px = (p_lng - a_lng) * cos_lat
    py = p_lat - a_lat
    t = (px * dx + py * dy) / seg_len_sq
    t_clamped = max(0.0, min(1.0, t))

    proj_lat = a_lat + t_clamped * (b_lat - a_lat)
    proj_lng = a_lng + t_clamped * (b_lng - a_lng)
    return proj_lat, proj_lng, t_clamped


def snap_point_to_polyline(lat: float, lng: float, polyline: List[List[float]]) -> Dict[str, Any]:
    """Finds the nearest point on polyline to given (lat, lng) and returns distance & progress."""
    if not polyline:
        return {
            "snapped_lat": lat,
            "snapped_lng": lng,
            "distance_km": 0.0,
            "distance_m": 0.0,
            "segment_index": 0,
            "progress_ratio": 0.0
        }

    if len(polyline) == 1:
        d_km = haversine_distance(lat, lng, polyline[0][0], polyline[0][1])
        return {
            "snapped_lat": polyline[0][0],
            "snapped_lng": polyline[0][1],
            "distance_km": round(d_km, 3),
            "distance_m": round(d_km * 1000.0, 1),
            "segment_index": 0,
            "progress_ratio": 0.0
        }

    min_dist_km = float("inf")
    best_lat, best_lng = polyline[0][0], polyline[0][1]
    best_seg_idx = 0
    best_t = 0.0

    # Total polyline length for global progress calculation
    cum_lens = [0.0]
    total_len = 0.0
    for i in range(len(polyline) - 1):
        seg_d = haversine_distance(polyline[i][0], polyline[i][1], polyline[i+1][0], polyline[i+1][1])
        total_len += seg_d
        cum_lens.append(total_len)

    for i in range(len(polyline) - 1):
        a_lat, a_lng = polyline[i][0], polyline[i][1]
        b_lat, b_lng = polyline[i+1][0], polyline[i+1][1]
        proj_lat, proj_lng, t = _project_point_to_segment(lat, lng, a_lat, a_lng, b_lat, b_lng)
        d_km = haversine_distance(lat, lng, proj_lat, proj_lng)

        if d_km < min_dist_km:
            min_dist_km = d_km
            best_lat = proj_lat
            best_lng = proj_lng
            best_seg_idx = i
            best_t = t

    # Calculate overall progress ratio along polyline (0.0 at start to 1.0 at destination)
    seg_start_dist = cum_lens[best_seg_idx]
    seg_length = (cum_lens[best_seg_idx + 1] - cum_lens[best_seg_idx]) if (best_seg_idx + 1 < len(cum_lens)) else 0.0
    point_dist_from_start = seg_start_dist + best_t * seg_length
    progress_ratio = (point_dist_from_start / total_len) if total_len > 0 else 0.0

    return {
        "snapped_lat": round(best_lat, 6),
        "snapped_lng": round(best_lng, 6),
        "distance_km": round(min_dist_km, 3),
        "distance_m": round(min_dist_km * 1000.0, 1),
        "segment_index": best_seg_idx,
        "progress_ratio": round(progress_ratio, 4)
    }
