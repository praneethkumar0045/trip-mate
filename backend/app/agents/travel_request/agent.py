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

    except Exception as e:
        raise ValueError(f"Failed to extract travel request: {e}") from e

    return {
        "origin": result.origin,
        "destination": result.destination,
        "trip_duration": result.trip_duration,
        "travel_dates": result.travel_dates,
        "travelers": result.travelers,
        "budget": result.budget,
    }
