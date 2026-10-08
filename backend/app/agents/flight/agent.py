from app.llm.factory import get_llm
from app.agents.flight.prompts import FLIGHT_AGENT_PROMPT

llm = get_llm()


def flight_agent(state):

    user_query = state["user_query"]

    prompt = FLIGHT_AGENT_PROMPT.format(
        user_query=user_query
    )

    response = llm.invoke(prompt)

    completed_agents = state.get(
        "completed_agents",
        []
    )

    return {
        "flight_results": [
            response.content
        ],
        "completed_agents": [
            *completed_agents,
            "flight"
        ]
    }
