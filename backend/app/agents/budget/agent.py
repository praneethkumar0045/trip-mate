import json
import sys
from pathlib import Path
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.graph.state import TravelState


def parse_mcp_result(result: Any) -> dict:
    """Convert MCP text content into a Python dictionary."""
    if isinstance(result, dict):
        return result

    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict) and item.get("type") == "text":
                try:
                    parsed = json.loads(item["text"])
                    if isinstance(parsed, dict):
                        return parsed
                except (KeyError, json.JSONDecodeError):
                    continue

    return {
        "status": "error",
        "message": "Could not parse the MCP budget tool response.",
    }


async def budget_agent(state: TravelState) -> dict:
    """Calculate a budget using the TripMate MCP server."""

    travelers = state.get("travelers")
    duration = state.get("trip_duration")

    # Do not invent traveler counts or trip duration.
    if not travelers or not duration:
        return {
            "budget_result": {
                "status": "missing_inputs",
                "missing_fields": [
                    name
                    for name, value in [
                        ("travelers", travelers),
                        ("trip_duration", duration),
                    ]
                    if not value
                ],
            }
        }

    # Assumption: trip_duration represents days.
    # A 5-day trip is treated as 4 nights.
    nights = max(duration - 1, 0)

    server_path = Path(__file__).resolve().parents[2] / "mcp_server" / "server.py"

    client = MultiServerMCPClient(
        {
            "tripmate": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(server_path)],
            }
        }
    )

    try:
        tools = await client.get_tools()

        budget_tool = next(
            (tool for tool in tools if tool.name == "calculate_trip_budget"),
            None,
        )

        if budget_tool is None:
            return {
                "budget_result": {
                    "status": "error",
                    "message": "MCP budget tool was not discovered.",
                }
            }

        result = await budget_tool.ainvoke(
            {
                "travelers": travelers,
                "nights": nights,
                "hotel_per_person_per_night": state.get("hotel_per_person_per_night"),
                "food_per_person_per_day": state.get("food_per_person_per_day"),
                "activities_per_person": state.get("activities_per_person"),
                "transport_total": state.get("transport_total"),
            }
        )

        budget_result = parse_mcp_result(result)

        print("[BUDGET] MCP result:", budget_result.get("status"))

        return {"budget_result": budget_result}

    except Exception as exc:
        # Keep provider/protocol errors visible in graph state.
        print(f"[BUDGET] MCP call failed: {type(exc).__name__}: {exc}")

        return {
            "budget_result": {
                "status": "error",
                "message": "The MCP budget tool could not be executed.",
            }
        }
