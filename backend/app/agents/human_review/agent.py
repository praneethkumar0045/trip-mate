
from langgraph.types import interrupt


def human_review_agent(state):
    decision = interrupt({
        "type": "itinerary_review",
        "message": "Review the travel itinerary before finalizing.",
        "itinerary": state.get("itinerary"),
        "validation": state.get("validation_result"),
    })

    if not isinstance(decision, dict):
        decision = {"approved": False, "feedback": ""}

    return {
        "human_decision": (
            "approve" if decision.get("approved") is True else "revise"
        ),
        "human_feedback": decision.get("feedback", ""),
    }
