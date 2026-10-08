from langgraph.graph import StateGraph, START, END

from app.graph.state import TravelState
from app.graph.routing import route_next_agent

from app.agents.supervisor.agent import supervisor_agent
from app.agents.flight.agent import flight_agent
from app.agents.hotel.agent import hotel_agent


def build_graph():

    graph = StateGraph(TravelState)

    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("flight", flight_agent)
    graph.add_node("hotel", hotel_agent)

    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_next_agent,
        {
            "flight": "flight",
            "hotel": "hotel",
            "weather": END,
            "location": END,
            "itinerary": END,
            "final": END,
        },
    )

    # IMPORTANT:
    # Flight goes back to Supervisor
    graph.add_edge("flight", "supervisor")
    graph.add_edge("hotel", "supervisor")
    
    return graph.compile()


travel_graph = build_graph()
