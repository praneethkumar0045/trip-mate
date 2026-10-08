def route_next_agent(state):

    next_agent = state.get("next_agent")

    valid_agents = {
        "flight",
        "hotel",
        "weather",
        "location",
        "itinerary",
        "final",
    }

    if next_agent not in valid_agents:
        raise ValueError(f"Invalid agent selected: {next_agent}")

    return next_agent
