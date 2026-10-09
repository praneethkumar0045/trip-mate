from app.graph.state import TravelState


def validation_failed_agent(state: TravelState) -> dict:
    """Stop safely when the itinerary cannot pass validation."""
    validation = state.get("validation_result") or {}
    issues = validation.get("issues") or [
        "The itinerary could not be validated successfully."
    ]

    message = (
        "I could not safely finalize this itinerary because validation "
        "did not pass within the allowed number of attempts.\n\n"
        "Please review and correct these issues before using the plan:\n"
        + "\n".join(f"- {issue}" for issue in issues)
    )

    completed_agents = list(state.get("completed_agents") or [])

    if "validation_failed" not in completed_agents:
        completed_agents.append("validation_failed")

    print("[VALIDATION] Finalization blocked: validation did not pass.")

    return {
        "final_response": message,
        "completed_agents": completed_agents,
    }
