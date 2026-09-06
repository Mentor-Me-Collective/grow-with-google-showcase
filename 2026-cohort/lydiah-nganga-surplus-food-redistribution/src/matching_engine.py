"""
matching_engine.py

Scores available NGOs/collection points against a new surplus food listing
and returns the best match, based on:
  - proximity (closer is better)
  - urgency (shorter expiry window = higher priority)
  - commodity weight (informed by FAO food-loss data: some food types
    historically go to waste faster, so they get a small priority boost)
  - NGO remaining capacity (can't match if the NGO can't take the load)

This is intentionally simple and explainable for an MVP demo — the scoring
logic is the "product" here, not a black box.
"""

import json
import math
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line distance between two lat/lon points, in kilometers."""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def score_ngo(ngo, listing_lat, listing_lon, quantity_kg, expiry_hours, commodity_weight):
    """
    Lower distance -> higher score.
    Shorter expiry window -> higher score (more urgent).
    Higher commodity_weight -> higher score.
    NGOs without enough remaining capacity are disqualified (return None).
    """
    if ngo["capacity_kg"] < quantity_kg:
        return None

    distance = haversine_km(listing_lat, listing_lon, ngo["lat"], ngo["lon"])

    # Normalize: closer = better. Cap distance influence at 30km for MVP scoring.
    distance_score = max(0, 30 - distance) / 30

    # Normalize urgency: anything under 6 hours is treated as maximum urgency.
    urgency_score = max(0, (24 - min(expiry_hours, 24))) / 24

    # Capacity headroom: NGOs with more spare room score slightly higher
    # (avoids always picking the smallest NGO down to the wire).
    capacity_score = min(ngo["capacity_kg"] / (quantity_kg * 3), 1)

    total = (
        distance_score * 0.45
        + urgency_score * 0.30
        + capacity_score * 0.10
        + (commodity_weight - 1.0) * 0.15  # small nudge, not a dominant factor
    )

    return {
        "ngo": ngo,
        "distance_km": round(distance, 2),
        "score": round(total, 3),
    }


def find_best_match(listing):
    """
    listing = {
        "food_type": str,
        "quantity_kg": float,
        "expiry_hours": float,
        "lat": float,
        "lon": float,
        "country": str,
    }
    Returns the best-matching NGO result dict, or None if nothing qualifies.
    """
    ngos = load_json("ngos.json")
    weights = load_json("commodity_weights.json")
    commodity_weight = weights.get(listing["food_type"], weights.get("Other", 1.0))

    # Only consider NGOs in the same country as the listing -- distance scoring
    # alone doesn't stop at borders, so this is a hard filter, not a soft one.
    same_country_ngos = [n for n in ngos if n.get("country") == listing.get("country")]

    candidates = []
    for ngo in same_country_ngos:
        result = score_ngo(
            ngo,
            listing["lat"],
            listing["lon"],
            listing["quantity_kg"],
            listing["expiry_hours"],
            commodity_weight,
        )
        if result:
            candidates.append(result)

    if not candidates:
        return None

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[0]