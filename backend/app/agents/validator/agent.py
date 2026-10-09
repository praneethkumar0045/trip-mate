import json
import re
from time import perf_counter

from app.llm.factory import get_llm
from app.agents.validator.prompts import VALIDATOR_PROMPT

# Initialize the LLM once when the module is imported.
llm = get_llm(max_tokens=300)


def normalize_itinerary(itinerary):
    """Convert itinerary state into a string."""
    if isinstance(itinerary, dict):
        return itinerary.get("content", str(itinerary))

    return itinerary or ""


def parse_validator_response(content):
    """Parse and validate the JSON returned by the LLM."""
    content = content.strip()

    # Handle JSON wrapped in Markdown code fences.
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    result = json.loads(content)

    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")

    if result.get("status") not in ("pass", "revise"):
        raise ValueError("Invalid validation status")

    score = result.get("score")

    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not 0 <= score <= 100
    ):
        raise ValueError("Invalid validation score")

    for key in ("issues", "warnings"):
        if not isinstance(result.get(key), list):
            raise ValueError(f"{key} must be a list")

        if not all(isinstance(item, str) for item in result[key]):
            raise ValueError(f"{key} must contain strings")

    if not isinstance(result.get("summary"), str):
        raise ValueError("summary must be a string")

    return result


def validator_agent(state):
    """Validate the generated itinerary and record execution timings."""
    total_start = perf_counter()

    itinerary = normalize_itinerary(state.get("itinerary"))

    # Deterministic checks do not require an LLM call.
    deterministic_issues = []

    if not state.get("destination"):
        deterministic_issues.append("Destination is missing.")

    duration = state.get("trip_duration")

    if isinstance(duration, bool) or not isinstance(duration, int) or duration < 1:
        deterministic_issues.append("Trip duration must be a positive integer.")

    if not itinerary.strip():
        deterministic_issues.append("Itinerary is empty.")

    # Build the validation prompt from the available research.
    prompt = VALIDATOR_PROMPT.format(
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
        itinerary=itinerary,
    )

    # NEW: measure the prompt size before sending it to the LLM.
    print(f"[PERF] Validator prompt characters: {len(prompt):,}")

    attempts = state.get("validation_attempts", 0) + 1

    try:
        # Measure the actual LLM request.
        llm_start = perf_counter()
        response = llm.invoke(prompt)
        llm_elapsed = perf_counter() - llm_start

        print(f"[PERF] Validator LLM call: {llm_elapsed:.2f}s")

        # NEW: measure the response size returned by the LLM.
        print(f"[PERF] Validator response characters: " f"{len(response.content):,}")

        # Measure JSON parsing separately.
        parse_start = perf_counter()
        result = parse_validator_response(response.content)
        parse_elapsed = perf_counter() - parse_start

        print(f"[PERF] Validator JSON parsing: {parse_elapsed:.4f}s")

        # Merge deterministic issues with LLM-reported issues.
        issues = list(dict.fromkeys(deterministic_issues + result["issues"]))

        result["issues"] = issues

        # Any blocking issue requires itinerary revision.
        if issues:
            result["status"] = "revise"

    except Exception as exc:
        # Fail closed: do not mark an unreliable validation as passed.
        print(f"[VALIDATOR] Validation failed: " f"{type(exc).__name__}: {exc}")

        result = {
            "status": "revise",
            "score": 0,
            "issues": list(
                dict.fromkeys(
                    deterministic_issues
                    + ["Validator failed to produce a reliable result."]
                )
            ),
            "warnings": [],
            "summary": "Validation could not be completed reliably.",
        }

    # Preserve existing completion tracking.
    completed_agents = list(state.get("completed_agents") or [])

    if "validator" not in completed_agents:
        completed_agents.append("validator")

    # Print total runtime before returning the state update.
    print(f"[PERF] Validator total execution: " f"{perf_counter() - total_start:.2f}s")

    return {
        "validation_result": result,
        "validation_status": result["status"],
        "validation_feedback": result["issues"],
        "validation_attempts": attempts,
        "completed_agents": completed_agents,
    }
