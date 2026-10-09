def route_next_agent(state):
    completed = set(state.get("completed_agents", []))

    if "flight" not in completed:
        return "flight"

    if "hotel" not in completed:
        return "hotel"

    if "location" not in completed:
        return "location"

    if "weather" not in completed:
        return "weather"

    # Once research is complete, generate the itinerary.
    return "itinerary"
