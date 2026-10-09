def filter_flight_evidence(results):
    """Keep flight status and the fields needed to validate claims."""
    if isinstance(results, dict):
        results = [results]

    filtered = []

    for item in results or []:
        if not isinstance(item, dict):
            continue

        entry = {
            key: item[key]
            for key in ("status", "source", "flight_date", "message")
            if key in item
        }

        flights = item.get("flights", [])

        if isinstance(flights, list):
            entry["flights"] = [
                {
                    key: flight[key]
                    for key in (
                        "airline",
                        "flight_number",
                        "status",
                        "departure",
                        "arrival",
                        "origin",
                        "destination",
                    )
                    if key in flight
                }
                for flight in flights
                if isinstance(flight, dict)
            ]

        filtered.append(entry)

    return filtered


def filter_hotel_evidence(results, max_chars=2500):
    """Preserve hotel agent output without treating it as verified data."""
    if isinstance(results, dict):
        results = [results]

    filtered = []

    for item in results or []:
        if isinstance(item, str):
            filtered.append(
                {
                    "type": "LLM-generated hotel suggestions",
                    "independently_verified": False,
                    "content": item[:max_chars],
                    "truncated": len(item) > max_chars,
                }
            )
        elif isinstance(item, dict):
            # Preserve status/error information if hotel output becomes
            # structured in a later implementation.
            filtered.append(
                {
                    key: item[key]
                    for key in (
                        "status",
                        "message",
                        "source",
                        "hotels",
                        "destination",
                    )
                    if key in item
                }
            )

    return filtered


def filter_weather_evidence(results):
    """Keep forecast dates and measurements relevant to the itinerary."""
    if isinstance(results, list):
        return [filter_weather_evidence(item) for item in results]

    if not isinstance(results, dict):
        return {"status": "unavailable"}

    filtered = {
        key: results[key]
        for key in (
            "status",
            "destination",
            "source",
            "timezone",
            "message",
        )
        if key in results
    }

    forecasts = results.get("forecasts")

    if isinstance(forecasts, list):
        filtered["forecasts"] = [
            {
                key: forecast[key]
                for key in (
                    "date",
                    "max_temp",
                    "min_temp",
                    "precipitation_probability",
                    "precipitation_sum",
                )
                if key in forecast
            }
            for forecast in forecasts
            if isinstance(forecast, dict)
        ]

    return filtered


def filter_location_evidence(results):
    """Keep geographic information relevant to destination validation."""
    if isinstance(results, dict):
        results = [results]

    allowed_fields = (
        "status",
        "name",
        "display_name",
        "latitude",
        "longitude",
        "lat",
        "lon",
        "address",
        "type",
        "message",
        "source",
    )

    filtered = []

    for item in results or []:
        if not isinstance(item, dict):
            continue

        filtered.append({key: item[key] for key in allowed_fields if key in item})

    return filtered
