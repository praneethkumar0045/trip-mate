import asyncio
from time import perf_counter
from langgraph.types import Command

from app.graph.graph import travel_graph


async def main():
    thread_id = "tripmate-hitl-test-001"

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    initial_state = {
        "user_query": "Plan a 5 day trip from Hyderabad to Goa",
        "origin": None,
        "destination": None,
        "trip_duration": 5,
        "travel_dates": None,
        "travelers": None,
        "budget": None,
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

    last_event_at = perf_counter()

    async for event in travel_graph.astream(
        initial_state, config=config, stream_mode="updates"
    ):
        now = perf_counter()
        elapsed = now - last_event_at
        last_event_at = now

        for node_name, update in event.items():
            print(
                f"Node: {node_name:<16} "
                f"Elapsed since previous event: {elapsed:.2f}s"
            )

            if node_name == "validator":
                print("Validation:", update.get("validation_status"))

            if node_name == "__interrupt__":
                print("Human review requested:", update)

    # Simulate the human approving the itinerary.
    print("\nSimulating human approval...")

    result = await travel_graph.ainvoke(
        Command(
            resume={
                "approved": True,
                "feedback": "",
            }
        ),
        config=config,
    )

    print("\nHuman decision:", result.get("human_decision"))
    print("Final response generated:", bool(result.get("final_response")))


if __name__ == "__main__":
    asyncio.run(main())


# async def main():
#     result = await travel_graph.ainvoke(
#         {
#             "user_query": "Plan a 5 day trip from Hyderabad to Goa",
#             "origin": None,
#             "destination": None,
#             "trip_duration": 5,
#             "travel_dates": None,
#             "travelers": None,
#             "budget": None,
#             "flight_results": [],
#             "hotel_results": [],
#             "weather_results": [],
#             "location_results": [],
#             "itinerary": None,
#             "completed_agents": [],
#             "next_agent": None,
#             "final_response": None,
#         }
#     )

#     print(result)


# if __name__ == "__main__":
#     asyncio.run(main())
