from pydantic import BaseModel, Field


class TravelRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Travel request from the user")

