from typing import TypedDict, Any


class TravelState(TypedDict):
    user_query: str

    origin: str | None
    destination: str | None

    trip_duration: int | None
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

    # New validator fields
    validation_result: dict | None
    validation_status: str | None
    validation_feedback: list[str]
    validation_attempts: int

    human_decision: str | None
    human_feedback: str | None
