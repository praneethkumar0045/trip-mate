from app.agents.weather.agent import weather_agent

state = {
    "user_query": "Plan a 5 day trip from Hyderabad to Goa",
    "destination": "Goa",
    "travel_dates": None,
    "trip_duration": 5,
    "completed_agents": [],
}

result = weather_agent(state)

print(result)
