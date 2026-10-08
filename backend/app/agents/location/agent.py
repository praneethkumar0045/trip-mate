from app.llm.factory import get_llm
from app.agents.location.prompts import LOCATION_AGENT_PROMPT
from app.tools.maps.nominatim import geocode_location

llm = get_llm()


async def location_agent(state):

    destination = state.get("destination")

    if not destination:
        prompt = LOCATION_AGENT_PROMPT.format(
            user_query=state["user_query"],
            destination="Not provided",
        )

        response = await llm.ainvoke(prompt)

        destination = response.content.strip()

    location = await geocode_location(destination)

    completed_agents = state.get("completed_agents", [])

    return {
        "location_results": [location] if location else [],
        "completed_agents": [*completed_agents, "location"],
    }
