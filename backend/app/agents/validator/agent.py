import json
import re
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.factory import get_llm
from app.agents.validator.prompts import VALIDATOR_PROMPT
from app.agents.validator.evidence import (
    filter_flight_evidence,
    filter_hotel_evidence,
    filter_weather_evidence,
    filter_location_evidence,
)

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


def validate_itinerary_structure(itinerary: str, trip_duration: int) -> list[str]:
    """Check day headings, missing days, and duplicate days."""
    issues = []

    # Supports headings such as:
    # ## Day 1: Arrival
    # **Day 2:** North Goa
    # Day 3 - Departure
    pattern = r"(?im)^\s*(?:#{1,6}\s*)?" r"(?:\*\*)?Day\s+(\d+)\b"

    day_numbers = [int(match.group(1)) for match in re.finditer(pattern, itinerary)]

    if not day_numbers:
        return ["No recognizable itinerary day headings were found."]

    # Find repeated day numbers.
    duplicates = sorted(
        number for number in set(day_numbers) if day_numbers.count(number) > 1
    )

    if duplicates:
        issues.append(f"Duplicate itinerary day headings: {duplicates}.")

    expected_days = set(range(1, trip_duration + 1))
    actual_days = set(day_numbers)

    missing_days = sorted(expected_days - actual_days)
    unexpected_days = sorted(actual_days - expected_days)

    if missing_days:
        issues.append(f"Missing itinerary day headings: {missing_days}.")

    if unexpected_days:
        issues.append(
            "Itinerary contains day headings outside the requested "
            f"duration: {unexpected_days}."
        )

    return issues


def compact_evidence(value, max_chars: int = 1200) -> str:
    """Serialize evidence and limit its size before prompting the LLM."""
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
        serialized[:max_chars]
        + "\n[Evidence truncated. Do not assume omitted information.]"
    )


def parse_validator_response(content: str) -> dict:
    """Parse the LLM response and validate it with Pydantic."""
    content = content.strip()

    # Support JSON wrapped in Markdown code fences.
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    validated = ValidationResult.model_validate_json(content)

    return validated.model_dump()


def build_validation_update(
    state: dict, result: dict, attempts: int, total_start: float
) -> dict:
    """Build a consistent LangGraph state update."""
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
    """Validate itinerary structure, research evidence, and consistency."""
    total_start = perf_counter()
    attempts = (state.get("validation_attempts") or 0) + 1

    itinerary = normalize_itinerary(state.get("itinerary"))
    deterministic_issues = []

    destination = state.get("destination")
    duration = state.get("trip_duration")

    # --------------------------------------------------
    # 1. Deterministic checks: no LLM required.
    # --------------------------------------------------
    if not isinstance(destination, str) or not destination.strip():
        deterministic_issues.append("Destination is missing.")

    valid_duration = (
        isinstance(duration, int) and not isinstance(duration, bool) and duration >= 1
    )

    if not valid_duration:
        deterministic_issues.append("Trip duration must be a positive integer.")

    if not itinerary.strip():
        deterministic_issues.append("Itinerary is empty.")

    # Check itinerary headings only when the duration is valid.
    if itinerary.strip() and valid_duration:
        deterministic_issues.extend(
            validate_itinerary_structure(itinerary=itinerary, trip_duration=duration)
        )

    # Stop early if required inputs or structure are invalid.
    if deterministic_issues:
        result = {
            "status": "revise",
            "score": 0,
            "issues": list(dict.fromkeys(deterministic_issues)),
            "warnings": [],
            "summary": (
                "Deterministic validation failed. Correct the reported "
                "issues before semantic validation."
            ),
        }

        return build_validation_update(state, result, attempts, total_start)

    # --------------------------------------------------
    # 2. Filter research evidence using actual agent formats.
    # --------------------------------------------------
    flight_evidence = filter_flight_evidence(state.get("flight_results") or [])

    hotel_evidence = filter_hotel_evidence(state.get("hotel_results") or [])

    weather_evidence = filter_weather_evidence(state.get("weather_results") or {})

    location_evidence = filter_location_evidence(state.get("location_results") or [])

    # --------------------------------------------------
    # 3. Build a bounded validation prompt.
    # --------------------------------------------------
    prompt = VALIDATOR_PROMPT.format(
        user_query=compact_evidence(state.get("user_query", ""), 1500),
        origin=state.get("origin") or "Not specified",
        destination=destination,
        trip_duration=duration,
        travel_dates=compact_evidence(
            state.get("travel_dates") or "Not specified", 500
        ),
        travelers=state.get("travelers") or "Not specified",
        budget=state.get("budget") or "Not specified",
        flight_results=compact_evidence(flight_evidence, 1200),
        hotel_results=compact_evidence(hotel_evidence, 1200),
        weather_results=compact_evidence(weather_evidence, 1000),
        location_results=compact_evidence(location_evidence, 1600),
        itinerary=itinerary[:6500],
    )

    print(f"[PERF] Validator prompt characters: {len(prompt):,}")

    # --------------------------------------------------
    # 4. Semantic validation with the LLM.
    # --------------------------------------------------
    try:
        llm_start = perf_counter()
        response = llm.invoke(prompt)
        llm_elapsed = perf_counter() - llm_start

        print(f"[PERF] Validator LLM call: {llm_elapsed:.2f}s")
        print(f"[PERF] Validator response characters: " f"{len(response.content):,}")

        parse_start = perf_counter()
        result = parse_validator_response(response.content)

        print(f"[PERF] Validator JSON parsing: " f"{perf_counter() - parse_start:.4f}s")

        # Deterministic issues override an LLM pass decision.
        result["issues"] = list(dict.fromkeys(deterministic_issues + result["issues"]))

        if result["issues"]:
            result["status"] = "revise"

    except Exception as exc:
        # Fail closed if the LLM or Pydantic validation fails.
        print(f"[VALIDATOR] Validation failed: " f"{type(exc).__name__}: {exc}")

        result = {
            "status": "revise",
            "score": 0,
            "issues": ["Validator failed to produce a reliable result."],
            "warnings": [],
            "summary": ("Validation could not be completed reliably."),
        }

    return build_validation_update(
        state,
        result,
        attempts,
        total_start,
    )
