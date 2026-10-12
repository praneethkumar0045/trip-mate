import math
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TripMate Travel Tools")


@mcp.tool()
def get_tripmate_status() -> dict[str, str]:
    """Return the current status of TripMate AI travel tools."""
    return {
        "service": "TripMate AI",
        "status": "ready",
        "message": "MCP server is working",
    }


@mcp.tool()
def calculate_trip_budget(
    travelers: int,
    nights: int,
    hotel_per_person_per_night: float | None = None,
    food_per_person_per_day: float | None = None,
    activities_per_person: float | None = None,
    transport_total: float | None = None,
) -> dict[str, Any]:
    """Calculate a trip budget using user-provided costs.

    Hotel: per person per night.
    Food: per person per day.
    Activities: per person for the whole trip.
    Transport: total for the entire group.

    Food is calculated for nights + 1 days. Missing costs are
    reported rather than estimated or invented.
    """
    if travelers < 1:
        return {
            "status": "error",
            "message": "Travelers must be at least 1.",
        }

    if nights < 0:
        return {
            "status": "error",
            "message": "Nights cannot be negative.",
        }

    costs = {
        "hotel_per_person_per_night": hotel_per_person_per_night,
        "food_per_person_per_day": food_per_person_per_day,
        "activities_per_person": activities_per_person,
        "transport_total": transport_total,
    }
    invalid_fields = [
        name
        for name, value in costs.items()
        if value is not None and (not math.isfinite(value) or value < 0)
    ]

    if invalid_fields:
        return {
            "status": "error",
            "message": "Costs must be finite, non-negative numbers.",
            "invalid_fields": invalid_fields,
        }

    missing_fields = [name for name, value in costs.items() if value is None]

    if missing_fields:
        return {
            "status": "missing_inputs",
            "missing_fields": missing_fields,
            "message": (
                "Provide all required costs before calculating " "the total budget."
            ),
        }

    hotel_total = travelers * nights * hotel_per_person_per_night
    food_days = nights + 1
    food_total = travelers * food_days * food_per_person_per_day
    activities_total = travelers * activities_per_person
    total = hotel_total + food_total + activities_total + transport_total

    return {
        "status": "success",
        "currency": "INR",
        "travelers": travelers,
        "nights": nights,
        "food_days": food_days,
        "breakdown": {
            "hotel": round(hotel_total, 2),
            "food": round(food_total, 2),
            "activities": round(activities_total, 2),
            "transport": round(transport_total, 2),
        },
        "total_budget": round(total, 2),
        "budget_per_person": round(total / travelers, 2),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
