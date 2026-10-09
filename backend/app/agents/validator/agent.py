import json
import re

from app.llm.factory import get_llm
from app.agents.validator.prompts import VALIDATOR_PROMPT

llm = get_llm()


def normalize_itinerary(itinerary):
    if isinstance(itinerary, dict):
        return itinerary.get("content", str(itinerary))

    return itinerary or ""


def parse_validator_response(content):
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    result = json.loads(content)

    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")

    if result.get("status") not in ("pass", "revise"):
        raise ValueError("Invalid validation status")

    if (
        isinstance(result.get("score"), bool)
        or not isinstance(result.get("score"), (int, float))
        or not 0 <= result["score"] <= 100
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
    itinerary = normalize_itinerary(state.get("itinerary"))

    deterministic_issues = []

    if not state.get("destination"):
        deterministic_issues.append("Destination is missing.")

    duration = state.get("trip_duration")

    if isinstance(duration, bool) or not isinstance(duration, int) or duration < 1:
        deterministic_issues.append("Trip duration must be a positive integer.")

    if not itinerary.strip():
        deterministic_issues.append("Itinerary is empty.")

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

    attempts = state.get("validation_attempts", 0) + 1

    try:
        response = llm.invoke(prompt)
        result = parse_validator_response(response.content)

        issues = list(dict.fromkeys(deterministic_issues + result["issues"]))

        result["issues"] = issues

        if issues:
            result["status"] = "revise"

    except Exception:
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
            "summary": "Validation could not be completed.",
        }

    completed_agents = list(state.get("completed_agents") or [])

    if "validator" not in completed_agents:
        completed_agents.append("validator")

    return {
        "validation_result": result,
        "validation_status": result["status"],
        "validation_feedback": result["issues"],
        "validation_attempts": attempts,
        "completed_agents": completed_agents,
    }
