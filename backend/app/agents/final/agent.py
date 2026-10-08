from app.llm.factory import get_llm
from app.agents.final.prompts import FINAL_RESPONSE_PROMPT

llm = get_llm()


def final_agent(state):

    prompt = FINAL_RESPONSE_PROMPT.format(
        user_query=state["user_query"],
        origin=state.get("origin"),
        destination=state.get("destination"),
        trip_duration=state.get("trip_duration"),
        travel_dates=state.get("travel_dates"),
        travelers=state.get("travelers"),
        budget=state.get("budget"),
        flight_results=state.get("flight_results", []),
        hotel_results=state.get("hotel_results", []),
        weather_results=state.get("weather_results", []),
        location_results=state.get("location_results", []),
        itinerary=state.get("itinerary"),
    )

    response = llm.invoke(prompt)

    return {"final_response": response.content}
