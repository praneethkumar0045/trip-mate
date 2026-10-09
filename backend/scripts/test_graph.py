import asyncio

from app.graph.graph import travel_graph


async def main():
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
    }

    async for event in travel_graph.astream(initial_state, stream_mode="updates"):
        for node_name, update in event.items():
            print(f"Node executed: {node_name}")
            if node_name == "validator":
                print("Validation:", update.get("validation_status"))
            if node_name == "final":
                print("Final response generated:", bool(update.get("final_response")))


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
