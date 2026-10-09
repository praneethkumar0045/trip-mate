from time import perf_counter

from app.llm.factory import get_llm
from app.agents.itinerary.prompts import ITINERARY_AGENT_PROMPT

# Initialize the LLM once when the module is imported.
llm = get_llm()


def normalize_itinerary(itinerary) -> str:
    """Extract itinerary text from the LangGraph state."""
    if isinstance(itinerary, dict):
        return itinerary.get("content", "")

    if isinstance(itinerary, str):
        return itinerary

    return ""


def itinerary_agent(state: dict) -> dict:
    """Generate or revise an itinerary using validator feedback."""

    feedback = state.get("validation_feedback") or []
    previous_itinerary = normalize_itinerary(state.get("itinerary"))

    # Build the normal itinerary-generation prompt.
    prompt = ITINERARY_AGENT_PROMPT.format(
        user_query=state.get("user_query", ""),
        origin=state.get("origin") or "Not specified",
        destination=state.get("destination") or "Not specified",
        trip_duration=state.get("trip_duration") or "Not specified",
        travel_dates=state.get("travel_dates") or "Not specified",
        travelers=state.get("travelers") or "Not specified",
        budget=state.get("budget") or "Not specified",
        flight_results=state.get("flight_results") or [],
        hotel_results=state.get("hotel_results") or [],
        weather_results=state.get("weather_results") or [],
        location_results=state.get("location_results") or [],
    )

    # Add revision instructions only when validation found problems.
    if feedback:
        prompt += (
            "\n\nREVISION MODE\n"
            "A previous itinerary failed validation. Revise it to address "
            "every actionable issue listed below.\n\n"
            "PREVIOUS ITINERARY:\n"
            f"{previous_itinerary[:6500] or 'No previous itinerary available.'}\n\n"
            "VALIDATOR FEEDBACK:\n"
            + "\n".join(f"- {issue}" for issue in feedback)
            + "\n\nREVISION RULES:\n"
            "- Address each reported issue explicitly.\n"
            "- Preserve correct information and useful activities.\n"
            "- Ensure the itinerary has the requested number of days.\n"
            "- Do not invent flight, hotel, price, or weather facts.\n"
            "- Use supplied research as evidence, not assumptions.\n"
            "- Disclose unavailable or unverified information.\n"
            "- Return the complete revised itinerary, not just a patch.\n"
        )
        print(f"[ITINERARY] Revision mode: " f"{len(feedback)} validation issue(s)")
    else:
        print("[ITINERARY] Initial generation mode")

    # Measure prompt size and LLM latency.
    print(f"[PERF] Itinerary prompt characters: {len(prompt):,}")

    start = perf_counter()
    response = llm.invoke(prompt)
    elapsed = perf_counter() - start

    print(f"[PERF] Itinerary LLM call: {elapsed:.2f}s")
    print(f"[PERF] Itinerary response characters: " f"{len(response.content):,}")

    completed_agents = list(state.get("completed_agents") or [])

    if "itinerary" not in completed_agents:
        completed_agents.append("itinerary")

    # Do not reset validation_attempts here. The graph uses it to
    # enforce the bounded validation-retry policy.
    return {
        "itinerary": {"content": response.content},
        "completed_agents": completed_agents,
        "validation_result": None,
        "validation_status": None,
        "validation_feedback": [],
    }
