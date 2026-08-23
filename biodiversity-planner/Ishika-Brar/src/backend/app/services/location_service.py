import requests


BASE_URL = "https://nominatim.openstreetmap.org/search"


def get_coordinates(location: str):

    params = {
        "q": location,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "BiodiversityPlanner/1.0"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        headers=headers
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return None

    return {
        "latitude": float(data[0]["lat"]),
        "longitude": float(data[0]["lon"])
    }