import httpx

BASE_URL = "https://api.open-meteo.com/v1/forecast"


async def get_weather(
    latitude: float, longitude: float, forecast_days: int = 5
) -> dict:
    if not 1 <= forecast_days <= 16:
        raise ValueError("forecast_days must be between 1 and 16")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "precipitation_sum",
        ],
        "forecast_days": forecast_days,
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    if "error" in data:
        raise RuntimeError(data.get("reason", "Weather API error"))

    daily = data.get("daily")
    if not daily or not daily.get("time"):
        raise RuntimeError("Weather API returned no daily forecast")

    return {
        "source": "Open-Meteo",
        "latitude": latitude,
        "longitude": longitude,
        "timezone": data.get("timezone"),
        "daily": daily,
    }
