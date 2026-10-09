import httpx

from app.core.config import settings

BASE_URL = "https://api.aviationstack.com/v1/flights"


async def search_flights(
    origin: str, destination: str, flight_date: str | None = None
) -> dict:
    if not settings.AVIATIONSTACK_API_KEY:
        raise RuntimeError("AVIATIONSTACK_API_KEY is not configured")

    params = {
        "access_key": settings.AVIATIONSTACK_API_KEY,
        "dep_iata": origin,
        "arr_iata": destination,
        "limit": 10,
    }

    if flight_date:
        params["flight_date"] = flight_date

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    if "error" in data:
        raise RuntimeError(f"AviationStack API error: {data['error']}")

    return {
        "source": "AviationStack",
        "origin": origin,
        "destination": destination,
        "flight_date": flight_date,
        "results": data.get("data", []),
        "count": data.get("pagination", {}).get("count", 0),
    }
