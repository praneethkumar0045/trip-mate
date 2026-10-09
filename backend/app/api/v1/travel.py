from fastapi import APIRouter, HTTPException
import uuid
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
            "validation_attempts": 0,
            "validation_status": None,
            "validation_result": None,
            "validation_feedback": [],
        }
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        result = await travel_graph.ainvoke(initial_state, config=config)

        # LangGraph pauses here when human review is required.
        if result.get("__interrupt__"):
            interrupt_data = result["__interrupt__"][0].value

            return {
                "query": request.query,
                "status": "human_review_required",
                "travel_plan": interrupt_data.get("itinerary"),
                "review": {
                    "type": interrupt_data.get("type"),
                    "message": interrupt_data.get("message"),
                    "validation": interrupt_data.get("validation"),
                },
                "completed_agents": result.get("completed_agents", []),
            }

        # Never report success if there is no final response.
        final_response = result.get("final_response")

        if not final_response:
            raise HTTPException(
                status_code=500,
                detail="The travel plan workflow ended without a response.",
            )

        validation_status = result.get("validation_status")

        # Distinguish safe-stop failure from successful finalization.
        if validation_status != "pass":
            return {
                "query": request.query,
                "status": "validation_failed",
                "travel_plan": None,
                "message": final_response,
                "validation": result.get("validation_result"),
                "completed_agents": result.get("completed_agents", []),
            }

        return {
            "query": request.query,
            "status": "success",
            "travel_plan": final_response,
            "completed_agents": result.get("completed_agents", []),
            "missing_details": {
                "travel_dates": result.get("travel_dates"),
                "travelers": result.get("travelers"),
                "budget": result.get("budget"),
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        # Keep the detailed exception in server logs.
        print(f"[API] Travel plan generation failed: {type(exc).__name__}: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to generate travel plan. Please try again.",
        ) from exc
