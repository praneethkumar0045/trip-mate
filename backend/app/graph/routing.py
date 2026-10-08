def route_next_agent(state):
    completed = set(state.get("completed_agents", []))

    if "flight" not in completed:
        return "flight"

    if "hotel" not in completed:
        return "hotel"

    if "weather" not in completed:
        return "weather"

    if "location" not in completed:
        return "location"

    if "itinerary" not in completed:
        return "itinerary"

    return "final"
