import asyncio
from time import perf_counter

from langgraph.types import Command

from app.graph.graph import travel_graph


async def main():
    thread_id = "tripmate-mcp-integration-test-001"

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # Initial state: no individual costs were provided.
    initial_state = {
        "user_query": (
            "Plan a 5 day trip from Hyderabad to Goa for 2 travelers. "
            "Hotel costs ₹1500 per person per night, food costs ₹500 "
            "per person per day, activities cost ₹1000 per person for "
            "the entire trip, and total transport costs ₹4000."
        ),
        "origin": None,
        "destination": None,
        "trip_duration": 5,
        "travel_dates": None,
        "travelers": None,
        "budget": None,
        "hotel_per_person_per_night": None,
        "food_per_person_per_day": None,
        "activities_per_person": None,
        "transport_total": None,
        "budget_result": None,
        "flight_results": [],
        "hotel_results": [],
        "weather_results": [],
        "location_results": [],
        "itinerary": None,
        "completed_agents": [],
        "next_agent": None,
        "final_response": None,
        "validation_result": None,
        "validation_status": None,
        "validation_feedback": [],
        "validation_attempts": 0,
        "human_decision": None,
        "human_feedback": None,
    }

    print("=" * 65)
    print("TripMate AI - LangGraph + MCP Integration Test")
    print("=" * 65)

    last_event_at = perf_counter()
    review_required = False

    # Run the workflow until it finishes or pauses for human review.
    async for event in travel_graph.astream(
        initial_state,
        config=config,
        stream_mode="updates",
    ):
        now = perf_counter()
        elapsed = now - last_event_at
        last_event_at = now

        for node_name, update in event.items():
            print(f"Node: {node_name:<18} " f"Elapsed: {elapsed:.2f}s")

            if node_name == "travel_request":
                print("Origin:", update.get("origin"))
                print("Destination:", update.get("destination"))
                print("Duration:", update.get("trip_duration"))
                print("Travelers:", update.get("travelers"))

            elif node_name == "budget":
                budget_result = update.get("budget_result")

                print("\nMCP Budget Result:")
                print(budget_result)

                if not isinstance(budget_result, dict):
                    raise RuntimeError("Budget node did not return budget_result.")

                if budget_result.get("status") == "success":
                    print(
                        "Total budget:",
                        budget_result.get("total_budget"),
                    )
                    print(
                        "Per person:",
                        budget_result.get("budget_per_person"),
                    )

                elif budget_result.get("status") == "missing_inputs":
                    print(
                        "Budget not calculated. Missing:",
                        budget_result.get("missing_fields"),
                    )

                elif budget_result.get("status") == "error":
                    print(
                        "Budget tool error:",
                        budget_result.get("message"),
                    )

            elif node_name == "validator":
                print(
                    "Validation status:",
                    update.get("validation_status"),
                )
                print(
                    "Validation result:",
                    update.get("validation_result"),
                )

            elif node_name == "__interrupt__":
                review_required = True
                print("\nHuman review requested.")
                print("Interrupt details:", update)

    # Resume only if the graph actually paused for review.
    if review_required:
        print("\n" + "=" * 65)
        print("Simulating human approval")
        print("=" * 65)

        result = await travel_graph.ainvoke(
            Command(
                resume={
                    "approved": True,
                    "feedback": "",
                }
            ),
            config=config,
        )

    else:
        # Retrieve the graph's final state if it completed without
        # an interrupt.
        result = await travel_graph.aget_state(config)
        result = result.values

    print("\n" + "=" * 65)
    print("FINAL TEST RESULTS")
    print("=" * 65)

    print("\nHuman decision:", result.get("human_decision"))
    print("Validation status:", result.get("validation_status"))

    print("\nBudget result:")
    print(result.get("budget_result"))

    final_response = result.get("final_response")

    print("\nFinal response generated:", bool(final_response))

    if final_response:
        print("\nFinal response content:\n")
        print(final_response)

    print("\n" + "=" * 65)

    if not result.get("budget_result"):
        print("WARNING: No budget result was stored in graph state.")

    if not final_response:
        print("WARNING: The graph did not generate a final response.")
    else:
        print("Final response is available.")

    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
