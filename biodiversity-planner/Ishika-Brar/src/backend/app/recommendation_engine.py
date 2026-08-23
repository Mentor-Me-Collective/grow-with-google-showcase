MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def value_matches(user_value: str, plant_value: str) -> bool:
    return user_value.strip().lower() == plant_value.strip().lower()


def bloom_duration(bloom_start: str, bloom_end: str) -> int:
    start = MONTHS.get(bloom_start.lower())
    end = MONTHS.get(bloom_end.lower())

    if start is None or end is None:
        return 0

    if end >= start:
        return end - start + 1

    # Handles a bloom period crossing December.
    return (12 - start + 1) + end


def calculate_score(
    plant,
    user_sunlight: str,
    user_soil_type: str,
    user_moisture: str,
) -> int:

    score = 0

    # Growing-condition compatibility
    if value_matches(user_sunlight, plant["sun_needs"]):
        score += 30

    if value_matches(user_soil_type, plant["soil_type"]):
        score += 25

    if value_matches(user_moisture, plant["moisture"]):
        score += 20

    # Pollinator diversity
    pollinators = [
        p.strip()
        for p in str(plant["pollinators_supported"]).split(",")
        if p.strip()
    ]

    # Maximum of 15 points.
    score += min(len(pollinators) * 5, 15)

    # Longer bloom periods receive a small bonus.
    duration = bloom_duration(
        str(plant["bloom_start"]),
        str(plant["bloom_end"])
    )

    # Maximum of 10 points.
    score += min(duration * 2, 10)

    return score


def recommend_plants(
    plants,
    region: str,
    user_sunlight: str,
    user_soil_type: str,
    user_moisture: str,
    limit: int = 5,
):

    # The current dataset is scoped to the Maryland Piedmont.
    # This allows the region to be expanded later when more regional
    # datasets become available.
    native_plants = plants[
        plants["native_range"].str.lower() == region.strip().lower()
    ]

    recommendations = []

    for _, plant in native_plants.iterrows():

        score = calculate_score(
            plant,
            user_sunlight,
            user_soil_type,
            user_moisture,
        )

        pollinators = [
            p.strip()
            for p in str(
                plant["pollinators_supported"]
            ).split(",")
            if p.strip()
        ]

        recommendations.append({
            "species_id": str(plant["species_id"]),
            "common_name": str(plant["common_name"]),
            "scientific_name": str(plant["scientific_name"]),
            "native_range": str(plant["native_range"]),
            "bloom_start": str(plant["bloom_start"]),
            "bloom_end": str(plant["bloom_end"]),
            "sun_needs": str(plant["sun_needs"]),
            "soil_type": str(plant["soil_type"]),
            "moisture": str(plant["moisture"]),
            "pollinators_supported": pollinators,
            "hardiness_zones": str(plant["hardiness_zones"]),
            "source": str(plant["source"]),
            "source_url": str(plant["source_url"]),
            "score": score,
        })

    recommendations.sort(
        key=lambda plant: plant["score"],
        reverse=True
    )

    return recommendations[:limit]