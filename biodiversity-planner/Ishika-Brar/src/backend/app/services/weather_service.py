import requests

BASE_URL = "https://api.open-meteo.com/v1/forecast"

def get_weather(latitude: float, longitude: float):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,cloud_cover",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 1,
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    return response.json()


