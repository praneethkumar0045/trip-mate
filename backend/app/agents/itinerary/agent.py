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
    validation_feedback = state.get("validation_feedback") or []
    human_feedback = (state.get("human_feedback") or "").strip()
    previous_itinerary = normalize_itinerary(state.get("itinerary"))

    feedback = list(validation_feedback)

    if state.get("human_decision") == "revise" and human_feedback:
        feedback.append(f"Human reviewer feedback: {human_feedback}")

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

    if feedback:
        prompt += (
            "\n\nREVISION MODE\n"
            "Revise the previous itinerary using the feedback below.\n\n"
            "PREVIOUS ITINERARY:\n"
            f"{previous_itinerary[:6500] or 'No previous itinerary available.'}\n\n"
            "REVISION FEEDBACK:\n"
            + "\n".join(f"- {issue}" for issue in feedback)
            + "\n\nREVISION RULES:\n"
            "- Address every actionable feedback item.\n"
            "- Preserve correct information and useful activities.\n"
            "- Keep the requested trip duration.\n"
            "- Do not invent flight, hotel, price, or weather facts.\n"
            "- Disclose unavailable or unverified information.\n"
            "- Return the complete revised itinerary.\n"
        )
        print(f"[ITINERARY] Revision mode: {len(feedback)} feedback item(s)")
    else:
        print("[ITINERARY] Initial generation mode")

    print(f"[PERF] Itinerary prompt characters: {len(prompt):,}")

    start = perf_counter()
    response = llm.invoke(prompt)
    print(f"[PERF] Itinerary LLM call: {perf_counter() - start:.2f}s")
    print(f"[PERF] Itinerary response characters: {len(response.content):,}")

    completed_agents = list(state.get("completed_agents") or [])
    if "itinerary" not in completed_agents:
        completed_agents.append("itinerary")

    return {
        "itinerary": {"content": response.content},
        "completed_agents": completed_agents,
        "validation_result": None,
        "validation_status": None,
        "validation_feedback": [],
        "human_decision": None,
        "human_feedback": "",
    }
