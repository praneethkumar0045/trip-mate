from langgraph.graph import StateGraph, START, END

from app.graph.state import TravelState
from app.graph.routing import route_next_agent
from langgraph.checkpoint.memory import MemorySaver

from app.agents.travel_request.agent import travel_request_agent
from app.agents.supervisor.agent import supervisor_agent
from app.agents.flight.agent import flight_agent
from app.agents.hotel.agent import hotel_agent
from app.agents.weather.agent import weather_agent
from app.agents.location.agent import location_agent
from app.agents.itinerary.agent import itinerary_agent
from app.agents.validator.agent import validator_agent
from app.agents.final.agent import final_agent
from app.agents.human_review.agent import human_review_agent

MAX_VALIDATION_ATTEMPTS = 2


def route_after_validation(state: TravelState) -> str:
    status = state.get("validation_status")
    attempts = state.get("validation_attempts", 0)

    if status == "pass":
        return "human_review"

    if attempts < MAX_VALIDATION_ATTEMPTS:
        return "itinerary"

    return "human_review"


def route_after_human_review(state: TravelState) -> str:
    decision = state.get("human_decision")

    if decision == "approve":
        return "final"

    return "itinerary"


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
    graph.add_node("human_review", human_review_agent)
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
            "human_review": "human_review",
        },
    )

    graph.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "itinerary": "itinerary",
            "final": "final",
        },
    )
    graph.add_edge("final", END)

    checkpointer = MemorySaver()
    travel_graph = graph.compile(checkpointer=checkpointer)

    # return graph.compile()
    return travel_graph


travel_graph = build_graph()
