from app.tools.flights.aviationstack import search_flights

AIRPORT_CODES = {
    "hyderabad": "HYD",
    "goa": "GOI",
}


def flight_agent(state):
    origin = state.get("origin")
    destination = state.get("destination")
    travel_dates = state.get("travel_dates")
    completed_agents = state.get("completed_agents", [])

    # Required travel information is missing.
    if not origin or not destination or not travel_dates:
        return {
            "flight_results": [
                {
                    "status": "needs_clarification",
                    "message": (
                        "Please provide the travel date before "
                        "searching for flights."
                    ),
                }
            ],
            "completed_agents": [*completed_agents, "flight"],
        }

    origin_code = AIRPORT_CODES.get(origin.strip().lower())
    destination_code = AIRPORT_CODES.get(destination.strip().lower())

    if not origin_code or not destination_code:
        return {
            "flight_results": [
                {
                    "status": "unsupported_location",
                    "message": (
                        "Airport mapping is unavailable for the "
                        "provided origin or destination."
                    ),
                }
            ],
            "completed_agents": [*completed_agents, "flight"],
        }

    departure_date = travel_dates.get("departure_date")

    if not departure_date:
        return {
            "flight_results": [
                {
                    "status": "needs_clarification",
                    "message": "A departure date is required.",
                }
            ],
            "completed_agents": [*completed_agents, "flight"],
        }

    try:
        import asyncio

        results = asyncio.run(
            search_flights(
                origin=origin_code,
                destination=destination_code,
                flight_date=departure_date,
            )
        )

        flights = [
            {
                "airline": item.get("airline", {}).get("name"),
                "flight_number": item.get("flight", {}).get("iata"),
                "status": item.get("flight_status"),
                "departure": item.get("departure", {}).get("scheduled"),
                "arrival": item.get("arrival", {}).get("scheduled"),
                "origin": item.get("departure", {}).get("iata"),
                "destination": item.get("arrival", {}).get("iata"),
            }
            for item in results.get("results", [])
        ]

        flight_results = [
            {
                "status": "success" if flights else "no_results",
                "source": results["source"],
                "flight_date": departure_date,
                "flights": flights,
            }
        ]

    except Exception as exc:
        flight_results = [
            {
                "status": "error",
                "message": str(exc),
            }
        ]

    return {
        "flight_results": flight_results,
        "completed_agents": [*completed_agents, "flight"],
    }
