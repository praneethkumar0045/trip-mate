def supervisor_agent(state):
    """Pass control to the graph's deterministic routing function."""
    completed_agents = list(state.get("completed_agents") or [])

    return {
        "completed_agents": completed_agents,
    }
