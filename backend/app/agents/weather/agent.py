import asyncio

from app.tools.weather.open_meteo import get_weather


def weather_agent(state: dict) -> dict:
    """Fetch a real daily weather forecast for the destination."""

    destination = state.get("destination")
    locations = state.get("location_results") or []

    # The location agent should have already geocoded the destination.
    if isinstance(locations, dict):
        locations = [locations]

    location = next(
        (
            item
            for item in locations
            if isinstance(item, dict)
            and item.get("latitude") is not None
            and item.get("longitude") is not None
        ),
        None,
    )

    if not location:
        return {
            "weather_results": {
                "status": "unavailable",
                "message": (
                    "Destination coordinates are unavailable. "
                    "Weather forecast could not be retrieved."
                ),
                "destination": destination,
            },
            "completed_agents": [*(state.get("completed_agents") or []), "weather"],
        }

    try:
        trip_duration = state.get("trip_duration") or 5
        forecast_days = min(max(int(trip_duration), 1), 16)

        weather_data = asyncio.run(
            get_weather(
                latitude=float(location["latitude"]),
                longitude=float(location["longitude"]),
                forecast_days=forecast_days,
            )
        )

        daily = weather_data["daily"]

        forecasts = []
        for index, date in enumerate(daily["time"]):
            forecasts.append(
                {
                    "date": date,
                    "max_temp": daily["temperature_2m_max"][index],
                    "min_temp": daily["temperature_2m_min"][index],
                    "precipitation_probability": (
                        daily["precipitation_probability_max"][index]
                    ),
                    "precipitation_sum": daily["precipitation_sum"][index],
                }
            )

        result = {
            "status": "success",
            "destination": destination,
            "source": weather_data["source"],
            "timezone": weather_data["timezone"],
            "forecasts": forecasts,
        }

    except Exception as exc:
        result = {
            "status": "unavailable",
            "destination": destination,
            "message": f"Weather forecast retrieval failed: {exc}",
        }

    return {
        "weather_results": result,
        "completed_agents": [*(state.get("completed_agents") or []), "weather"],
    }
