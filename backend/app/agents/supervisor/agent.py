from app.llm.factory import get_llm
from app.agents.supervisor.prompts import SUPERVISOR_PROMPT
from app.schemas.agent import SupervisorDecision

llm = get_llm()
structured_llm = llm.with_structured_output(SupervisorDecision)


def supervisor_agent(state):

    user_query = state["user_query"]

    completed_agents = state.get("completed_agents", [])

    prompt = SUPERVISOR_PROMPT.format(
        user_query=user_query,
        completed_agents=", ".join(completed_agents) if completed_agents else "None",
    )

    decision = structured_llm.invoke(prompt)

    return {"next_agent": decision.next_agent}
