import asyncio
import json
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    server_path = (
        Path(__file__).resolve().parents[1] / "app" / "mcp_server" / "server.py"
    )

    client = MultiServerMCPClient(
        {
            "tripmate": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(server_path)],
            }
        }
    )

    # 1. Discover tools exposed by the MCP server.
    tools = await client.get_tools()
    tool_map = {tool.name: tool for tool in tools}

    print("Discovered MCP tools:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

    assert "get_tripmate_status" in tool_map
    assert "calculate_trip_budget" in tool_map

    print("\nPASS: Expected tools discovered.")

    # 2. Test the status tool.
    status_result = await tool_map["get_tripmate_status"].ainvoke({})

    print("\nStatus result:")
    print(status_result)

    # 3. Test a complete budget calculation.
    budget_result = await tool_map["calculate_trip_budget"].ainvoke(
        {
            "travelers": 2,
            "nights": 3,
            "hotel_per_person_per_night": 1500,
            "food_per_person_per_day": 500,
            "activities_per_person": 1000,
            "transport_total": 4000,
        }
    )

    print("\nComplete budget result:")
    print(budget_result)

    # The adapter returns MCP content blocks; parse its JSON text.
    def extract_result(result):
        if isinstance(result, dict):
            return result

        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        return json.loads(item["text"])
                    except (KeyError, json.JSONDecodeError):
                        continue

        raise AssertionError(f"Could not parse tool result: {result}")

    budget = extract_result(budget_result)

    assert budget["status"] == "success", budget
    assert budget["total_budget"] == 19000, budget
    assert budget["budget_per_person"] == 9500, budget

    print("PASS: Budget calculation is correct.")

    # 4. Verify missing costs do not produce a fabricated estimate.
    missing_result = await tool_map["calculate_trip_budget"].ainvoke(
        {
            "travelers": 2,
            "nights": 3,
        }
    )

    missing_budget = extract_result(missing_result)

    print("\nMissing-cost result:")
    print(missing_budget)

    assert missing_budget["status"] == "missing_inputs"
    assert len(missing_budget["missing_fields"]) == 4

    print("PASS: Missing costs are handled correctly.")

    # 5. Verify negative costs are rejected.
    invalid_result = await tool_map["calculate_trip_budget"].ainvoke(
        {
            "travelers": 2,
            "nights": 3,
            "hotel_per_person_per_night": -100,
            "food_per_person_per_day": 500,
            "activities_per_person": 1000,
            "transport_total": 4000,
        }
    )
    

    invalid_budget = extract_result(invalid_result)

    print("\nInvalid-cost result:")
    print(invalid_budget)

    assert invalid_budget["status"] == "error"

    print("PASS: Negative costs are rejected.")
    print("\nAll MCP client tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
