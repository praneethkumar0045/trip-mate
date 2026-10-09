import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langgraph.types import Command

from app.schemas.travel import TravelRequest
from app.graph.graph import travel_graph

router = APIRouter()


class HumanReviewRequest(BaseModel):
    approved: bool
    feedback: str = ""


def get_pending_review(result):
    interrupts = result.get("__interrupt__") or []
    if not interrupts:
        return None
    return interrupts[0].value


def build_response(query, thread_id, result):
    review = get_pending_review(result)

    if review is not None:
        return {
            "query": query,
            "thread_id": thread_id,
            "status": "human_review_required",
            "travel_plan": review.get("itinerary"),
            "review": {
                "type": review.get("type"),
                "message": review.get("message"),
                "validation": review.get("validation"),
            },
            "completed_agents": result.get("completed_agents", []),
        }

    final_response = result.get("final_response")

    if not final_response:
        raise HTTPException(
            status_code=500,
            detail="Workflow ended without a final response.",
        )

    if result.get("validation_status") != "pass":
        return {
            "query": query,
            "thread_id": thread_id,
            "status": "validation_failed",
            "travel_plan": None,
            "message": final_response,
            "validation": result.get("validation_result"),
            "completed_agents": result.get("completed_agents", []),
        }

    return {
        "query": query,
        "thread_id": thread_id,
        "status": "success",
        "travel_plan": final_response,
        "completed_agents": result.get("completed_agents", []),
        "missing_details": {
            "travel_dates": result.get("travel_dates"),
            "travelers": result.get("travelers"),
            "budget": result.get("budget"),
        },
    }


@router.post("/travel")
async def create_travel_plan(request: TravelRequest):
    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

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
        "human_decision": None,
        "human_feedback": "",
    }

    try:
        result = await travel_graph.ainvoke(
            initial_state,
            config=config,
        )
        return build_response(request.query, thread_id, result)

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[API] Travel creation failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate travel plan. Please try again.",
        ) from exc


@router.post("/travel/{thread_id}/review")
async def review_travel_plan(thread_id: str, request: HumanReviewRequest):
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    decision = {
        "approved": request.approved,
        "feedback": request.feedback,
    }

    try:
        # Resume the paused graph; do not start a new workflow.
        result = await travel_graph.ainvoke(
            Command(resume=decision),
            config=config,
        )

        return build_response(
            query=result.get("user_query", ""),
            thread_id=thread_id,
            result=result,
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[API] Travel review failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process itinerary review.",
        ) from exc
