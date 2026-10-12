import json

from app.llm.factory import get_llm
from app.schemas.travel_request import TravelRequest
from app.agents.travel_request.prompts import TRAVEL_REQUEST_PROMPT

llm = get_llm()


def travel_request_agent(state):
    prompt = TRAVEL_REQUEST_PROMPT.format(user_query=state["user_query"])

    response = llm.invoke(prompt)

    try:
        data = json.loads(response.content)
        result = TravelRequest.model_validate(data)
    except Exception as exc:
        raise ValueError(f"Failed to extract travel request: {exc}") from exc

    return {
        "origin": result.origin,
        "destination": result.destination,
        "trip_duration": result.trip_duration,
        "travel_dates": result.travel_dates,
        "travelers": result.travelers,
        "budget": result.budget,
        "hotel_per_person_per_night": (result.hotel_per_person_per_night),
        "food_per_person_per_day": (result.food_per_person_per_day),
        "activities_per_person": result.activities_per_person,
        "transport_total": result.transport_total,
    }
