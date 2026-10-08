from fastapi import APIRouter
from app.schemas.travel import TravelRequest

router = APIRouter()


@router.post("/travel")
async def create_travel_plan(request: TravelRequest):
    return {"message": "Travel request received", "query": request.query}
