from typing import TypedDict


class TravelState(TypedDict):

    user_query: str

    origin: str | None
    destination: str | None
    travel_dates: dict | None
    travelers: int | None
    budget: str | None

    flight_results: list
    hotel_results: list
    weather_results: list
    location_results: list

    itinerary: dict | None

    completed_agents: list[str]

    next_agent: str | None

    final_response: str | None
