from langgraph.graph import StateGraph, START, END

from app.graph.state import TravelState
from app.graph.routing import route_next_agent

from app.agents.travel_request.agent import travel_request_agent
from app.agents.supervisor.agent import supervisor_agent
from app.agents.flight.agent import flight_agent
from app.agents.hotel.agent import hotel_agent
from app.agents.weather.agent import weather_agent
from app.agents.location.agent import location_agent
from app.agents.itinerary.agent import itinerary_agent
from app.agents.validator.agent import validator_agent
from app.agents.final.agent import final_agent

MAX_VALIDATION_ATTEMPTS = 2


def route_after_validation(state: TravelState) -> str:
    status = state.get("validation_status")
    attempts = state.get("validation_attempts", 0)

    if status == "pass":
        return "final"

    if attempts < MAX_VALIDATION_ATTEMPTS:
        return "itinerary"

    # Stop retrying after the configured limit.
    return "final"


def build_graph():

    graph = StateGraph(TravelState)

    graph.add_node("travel_request", travel_request_agent)
    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("flight", flight_agent)
    graph.add_node("hotel", hotel_agent)
    graph.add_node("weather", weather_agent)
    graph.add_node("location", location_agent)
    graph.add_node("itinerary", itinerary_agent)
    graph.add_node("validator", validator_agent)
    graph.add_node("final", final_agent)

    graph.add_edge(START, "travel_request")
    graph.add_edge("travel_request", "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_next_agent,
        {
            "flight": "flight",
            "hotel": "hotel",
            "weather": "weather",
            "location": "location",
            "itinerary": "itinerary",
            "final": "final",
        },
    )

    # IMPORTANT:
    # Flight goes back to Supervisor
    graph.add_edge("flight", "supervisor")
    graph.add_edge("hotel", "supervisor")
    graph.add_edge("location", "supervisor")
    graph.add_edge("weather", "supervisor")
  
    # Validate every generated itinerary.
    graph.add_edge("itinerary", "validator")

    # The validator controls retry or completion.
    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "itinerary": "itinerary",
            "final": "final",
        },
    )
    graph.add_edge("final", END)

    return graph.compile()


travel_graph = build_graph()
