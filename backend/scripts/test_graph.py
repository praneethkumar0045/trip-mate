import asyncio

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

    # Run until the graph pauses for human review.
    async for event in travel_graph.astream(
        initial_state, config=config, stream_mode="updates"
    ):
        for node_name, update in event.items():
            print(f"Node executed: {node_name}")

            if node_name == "validator":
                print("Validation:", update.get("validation_status"))

            if node_name == "__interrupt__":
                print("\nHuman review requested:")
                print(update)

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
