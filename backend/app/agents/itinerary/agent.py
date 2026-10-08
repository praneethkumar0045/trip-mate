from app.llm.factory import get_llm
from app.agents.itinerary.prompts import ITINERARY_AGENT_PROMPT

llm = get_llm()


def itinerary_agent(state):

    prompt = ITINERARY_AGENT_PROMPT.format(
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
    )

    response = llm.invoke(prompt)

    completed_agents = state.get("completed_agents", [])

    return {
        "itinerary": {"content": response.content},
        "completed_agents": [*completed_agents, "itinerary"],
    }
