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

    if "itinerary" not in completed:
        return "itinerary"

    # Do not route directly to final.
    # The itinerary node should lead to the validator,
    # and the validator decides whether to retry or finish.
    return "itinerary"
