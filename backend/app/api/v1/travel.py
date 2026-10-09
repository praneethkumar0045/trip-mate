from fastapi import APIRouter, HTTPException

from app.schemas.travel import TravelRequest
from app.graph.graph import travel_graph

router = APIRouter()


@router.post("/travel")
async def create_travel_plan(request: TravelRequest):
    try:
        initial_state = {
            "user_query": request.query,
            "origin": None,
            "destination": None,
            "trip_duration": None,
            "travel_dates": None,
            "travelers": None,
            "budget": None,
            "flight_results": [],
            "hotel_results": [],
            "weather_results": {},
            "location_results": [],
            "itinerary": None,
            "completed_agents": [],
            "next_agent": None,
            "final_response": None,
        }

        result = await travel_graph.ainvoke(initial_state)

        return {
            "query": request.query,
            "status": "success",
            "travel_plan": result.get("final_response"),
            "completed_agents": result.get("completed_agents", []),
            "missing_details": {
                "travel_dates": result.get("travel_dates"),
                "travelers": result.get("travelers"),
                "budget": result.get("budget"),
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate travel plan. Please try again.",
        ) from exc
