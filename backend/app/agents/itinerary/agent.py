from time import perf_counter

from app.llm.factory import get_llm
from app.agents.itinerary.prompts import ITINERARY_AGENT_PROMPT

llm = get_llm()


def itinerary_agent(state):
    prompt = ITINERARY_AGENT_PROMPT.format(
        user_query=state.get("user_query", ""),
        origin=state.get("origin"),
        destination=state.get("destination"),
        trip_duration=state.get("trip_duration"),
        travel_dates=state.get("travel_dates"),
        travelers=state.get("travelers"),
        budget=state.get("budget"),
        flight_results=state.get("flight_results") or [],
        hotel_results=state.get("hotel_results") or [],
        weather_results=state.get("weather_results") or [],
        location_results=state.get("location_results") or [],
    )

    feedback = state.get("validation_feedback") or []

    if feedback:
        prompt += (
            "\n\nVALIDATOR FEEDBACK — CORRECT THESE ISSUES:\n"
            + "\n".join(f"- {issue}" for issue in feedback)
            + "\nDo not invent missing facts to satisfy the validator. "
            "Clearly disclose information that cannot be verified."
        )

    # Instrumentation: measure prompt size and actual LLM latency.
    print(f"[PERF] Itinerary prompt characters: {len(prompt):,}")

    start = perf_counter()
    response = llm.invoke(prompt)
    elapsed = perf_counter() - start

    print(f"[PERF] Itinerary LLM call: {elapsed:.2f}s")
    print(f"[PERF] Itinerary response characters: " f"{len(response.content):,}")

    completed_agents = list(state.get("completed_agents") or [])

    if "itinerary" not in completed_agents:
        completed_agents.append("itinerary")

    return {
        "itinerary": {"content": response.content},
        "completed_agents": completed_agents,
        "validation_result": None,
        "validation_status": None,
        "validation_feedback": [],
    }
