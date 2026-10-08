import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def geocode_location(location: str):

    params = {
        "q": location,
        "format": "json",
        "limit": 1,
    }

    headers = {"User-Agent": "TripMate-AI/1.0"}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
        )

        response.raise_for_status()

        data = response.json()

    if not data:
        return None

    result = data[0]

    return {
        "name": result.get("display_name"),
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
    }
