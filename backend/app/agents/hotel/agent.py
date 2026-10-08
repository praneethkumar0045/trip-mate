from app.llm.factory import get_llm
from app.agents.hotel.prompts import HOTEL_AGENT_PROMPT

llm = get_llm()


def hotel_agent(state):

    prompt = HOTEL_AGENT_PROMPT.format(
        user_query=state["user_query"],
        destination=state.get("destination"),
        travel_dates=state.get("travel_dates"),
        travelers=state.get("travelers"),
        budget=state.get("budget"),
    )

    response = llm.invoke(prompt)

    completed_agents = state.get("completed_agents", [])

    return {
        "hotel_results": [response.content],
        "completed_agents": [*completed_agents, "hotel"],
    }
