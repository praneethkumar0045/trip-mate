from app.graph.graph import travel_graph

result = travel_graph.invoke(
    {
        "user_query": "Plan a 5 day trip from Hyderabad to Goa",
        "origin": None,
        "destination": None,
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
    }
)


print(result)
