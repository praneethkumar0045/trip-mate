from app.llm.factory import get_llm
from app.agents.weather.prompts import WEATHER_AGENT_PROMPT

llm = get_llm()


def weather_agent(state):

    prompt = WEATHER_AGENT_PROMPT.format(
        user_query=state["user_query"],
        destination=state.get("destination"),
        travel_dates=state.get("travel_dates"),
        trip_duration=state.get("trip_duration"),
    )

    response = llm.invoke(prompt)

    completed_agents = state.get("completed_agents", [])

    return {
        "weather_results": [response.content],
        "completed_agents": [*completed_agents, "weather"],
    }
