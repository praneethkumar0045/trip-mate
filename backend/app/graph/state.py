from typing import TypedDict, Any


class TravelState(TypedDict):
    user_query: str

    origin: str | None
    destination: str | None

    trip_duration: int | None
    travel_dates: dict | None
    travelers: int | None
    budget: str | None
    # Explicit budget calculator inputs.
    hotel_per_person_per_night: float | None
    food_per_person_per_day: float | None
    activities_per_person: float | None
    transport_total: float | None

    budget_result: dict | None

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
