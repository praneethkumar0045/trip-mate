from app.graph.graph import (
    route_after_validation,
    route_after_human_review,
    MAX_VALIDATION_ATTEMPTS,
)

state = {
    "validation_status": "revise",
    "validation_attempts": 1,
    "human_decision": None,
}

assert route_after_validation(state) == "itinerary"
print("PASS: Failed validation triggers a retry.")

state["validation_attempts"] = MAX_VALIDATION_ATTEMPTS
print("DEBUG: Max attempts =", MAX_VALIDATION_ATTEMPTS)
print("DEBUG: Route =", route_after_validation(state))

assert route_after_validation(state) == "validation_failed"
print("PASS: Retry limit blocks further generation.")

state["human_decision"] = "approve"
assert route_after_human_review(state) == "validation_failed"
print("PASS: Approval cannot bypass failed validation.")

state["validation_status"] = "pass"
assert route_after_human_review(state) == "final"
print("PASS: Validated and approved itinerary can finalize.")

print("\nAll routing tests passed.")
