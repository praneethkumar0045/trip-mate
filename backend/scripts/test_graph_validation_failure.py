from langgraph.graph import StateGraph, START, END

from app.graph.state import TravelState
from app.graph.graph import (
    MAX_VALIDATION_ATTEMPTS,
    route_after_validation,
)
from app.graph.graph import validation_failed_agent

# Track which nodes actually execute.
calls = {
    "itinerary": 0,
    "validator": 0,
    "human_review": 0,
    "final": 0,
}


def mock_itinerary_agent(state: TravelState) -> dict:
    """Simulate generating an itinerary on every attempt."""
    calls["itinerary"] += 1

    return {"itinerary": {"content": f"Test itinerary attempt {calls['itinerary']}"}}


def mock_validator_agent(state: TravelState) -> dict:
    """Simulate validation failing on every attempt."""
    calls["validator"] += 1
    attempts = (state.get("validation_attempts") or 0) + 1

    return {
        "validation_status": "revise",
        "validation_attempts": attempts,
        "validation_feedback": ["Missing required itinerary details."],
        "validation_result": {
            "status": "revise",
            "score": 0,
            "issues": ["Missing required itinerary details."],
            "warnings": [],
            "summary": "Test validation failure.",
        },
    }


def unexpected_human_review(state: TravelState) -> dict:
    calls["human_review"] += 1
    raise AssertionError(
        "Human review must not run after validation retries are exhausted."
    )


def unexpected_final_agent(state: TravelState) -> dict:
    calls["final"] += 1
    raise AssertionError("Final agent must not run when validation fails.")


def build_test_graph():
    graph = StateGraph(TravelState)

    graph.add_node("itinerary", mock_itinerary_agent)
    graph.add_node("validator", mock_validator_agent)
    graph.add_node("human_review", unexpected_human_review)
    graph.add_node("final", unexpected_final_agent)
    graph.add_node("validation_failed", validation_failed_agent)

    graph.add_edge(START, "itinerary")
    graph.add_edge("itinerary", "validator")

    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "itinerary": "itinerary",
            "human_review": "human_review",
            "validation_failed": "validation_failed",
        },
    )

    graph.add_edge("human_review", "final")
    graph.add_edge("final", END)
    graph.add_edge("validation_failed", END)

    return graph.compile()


def main():
    test_graph = build_test_graph()

    result = test_graph.invoke(
        {
            "completed_agents": [],
            "validation_attempts": 0,
            "validation_status": None,
            "validation_feedback": [],
            "validation_result": None,
            "final_response": None,
        }
    )

    assert calls["itinerary"] == MAX_VALIDATION_ATTEMPTS, (
        f"Expected {MAX_VALIDATION_ATTEMPTS} itinerary attempts, "
        f"got {calls['itinerary']}"
    )
    print("PASS: Itinerary retries stop at the configured limit.")

    assert calls["validator"] == MAX_VALIDATION_ATTEMPTS
    print("PASS: Validator ran once per itinerary attempt.")

    assert calls["human_review"] == 0
    print("PASS: Human review was not reached.")

    assert calls["final"] == 0
    print("PASS: Final agent was not called.")

    assert "could not safely finalize" in result["final_response"].lower()
    assert "Missing required itinerary details." in result["final_response"]
    print("PASS: Safe-stop message contains the validation issue.")

    assert result["validation_status"] == "revise"
    print("PASS: Failed validation status is preserved.")

    print("\nAll end-to-end failure-path tests passed.")


if __name__ == "__main__":
    main()
