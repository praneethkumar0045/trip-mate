import json
import re
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.factory import get_llm
from app.agents.validator.prompts import VALIDATOR_PROMPT

# Initialize the LLM once when the module is imported.
llm = get_llm(max_tokens=300)


class ValidationResult(BaseModel):
    """Validate the structure of the LLM's validation response."""

    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["pass", "revise"]
    score: int | float = Field(ge=0, le=100)
    issues: list[str]
    warnings: list[str]
    summary: str


def normalize_itinerary(itinerary) -> str:
    """Convert itinerary state into a safe string representation."""
    if isinstance(itinerary, dict):
        itinerary = itinerary.get("content", "")

    if itinerary is None:
        return ""

    if isinstance(itinerary, str):
        return itinerary

    return str(itinerary)


def compact_evidence(value, max_chars: int = 1200) -> str:
    """Limit research evidence included in the validation prompt."""
    if value is None:
        return "No evidence supplied."

    try:
        if isinstance(value, str):
            serialized = value
        else:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        serialized = str(value)

    if len(serialized) <= max_chars:
        return serialized

    return (
        serialized[:max_chars] + "\n[Evidence truncated to fit the validation context.]"
    )


def parse_validator_response(content: str) -> dict:
    """Parse the JSON and validate it against the Pydantic schema."""
    content = content.strip()

    # Support JSON wrapped in Markdown code fences.
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    validated = ValidationResult.model_validate_json(content)

    return validated.model_dump()


def build_validation_update(
    state: dict, result: dict, attempts: int, total_start: float
) -> dict:
    """Build the LangGraph state update consistently."""
    completed_agents = list(state.get("completed_agents") or [])

    if "validator" not in completed_agents:
        completed_agents.append("validator")

    print(f"[PERF] Validator total execution: " f"{perf_counter() - total_start:.2f}s")

    return {
        "validation_result": result,
        "validation_status": result["status"],
        "validation_feedback": result["issues"],
        "validation_attempts": attempts,
        "completed_agents": completed_agents,
    }


def validator_agent(state: dict) -> dict:
    """Validate itinerary structure, evidence, and semantic consistency."""
    total_start = perf_counter()
    attempts = (state.get("validation_attempts") or 0) + 1

    itinerary = normalize_itinerary(state.get("itinerary"))
    deterministic_issues = []

    destination = state.get("destination")
    duration = state.get("trip_duration")

    # Basic checks that do not require an LLM.
    if not isinstance(destination, str) or not destination.strip():
        deterministic_issues.append("Destination is missing.")

    if isinstance(duration, bool) or not isinstance(duration, int) or duration < 1:
        deterministic_issues.append("Trip duration must be a positive integer.")

    if not itinerary.strip():
        deterministic_issues.append("Itinerary is empty.")

    # Stop early when essential input is invalid.
    # There is no value in paying for semantic validation yet.
    if deterministic_issues:
        result = {
            "status": "revise",
            "score": 0,
            "issues": deterministic_issues,
            "warnings": [],
            "summary": (
                "Basic validation failed. Correct the issues "
                "before semantic validation."
            ),
        }

        return build_validation_update(state, result, attempts, total_start)

    # Keep the prompt focused by limiting raw research evidence.
    prompt = VALIDATOR_PROMPT.format(
        user_query=compact_evidence(state.get("user_query", ""), 1500),
        origin=state.get("origin") or "Not specified",
        destination=destination,
        trip_duration=duration,
        travel_dates=state.get("travel_dates") or "Not specified",
        travelers=state.get("travelers") or "Not specified",
        budget=state.get("budget") or "Not specified",
        flight_results=compact_evidence(state.get("flight_results") or [], 1200),
        hotel_results=compact_evidence(state.get("hotel_results") or [], 1200),
        weather_results=compact_evidence(state.get("weather_results") or [], 1000),
        location_results=compact_evidence(state.get("location_results") or [], 1600),
        itinerary=itinerary[:6500],
    )

    print(f"[PERF] Validator prompt characters: {len(prompt):,}")

    try:
        llm_start = perf_counter()
        response = llm.invoke(prompt)
        llm_elapsed = perf_counter() - llm_start

        print(f"[PERF] Validator LLM call: {llm_elapsed:.2f}s")
        print(f"[PERF] Validator response characters: " f"{len(response.content):,}")

        parse_start = perf_counter()
        result = parse_validator_response(response.content)
        print(f"[PERF] Validator JSON parsing: " f"{perf_counter() - parse_start:.4f}s")

        # Deterministic issues always override a passing LLM decision.
        result["issues"] = list(dict.fromkeys(deterministic_issues + result["issues"]))

        if result["issues"]:
            result["status"] = "revise"

    except Exception as exc:
        # Fail closed on LLM, JSON, or schema-validation failures.
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
            "summary": ("Validation could not be completed reliably."),
        }

    return build_validation_update(state, result, attempts, total_start)
