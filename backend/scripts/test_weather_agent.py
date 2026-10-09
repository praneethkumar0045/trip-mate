
import asyncio

from app.agents.weather.agent import weather_agent

state = {
    "destination": "Goa",
    "trip_duration": 5,
    "location_results": [
        {
            "name": "Goa, India",
            "latitude": 15.3004543,
            "longitude": 74.0855134,
        }
    ],
    "completed_agents": [],
}

result = weather_agent(state)
print(result)
