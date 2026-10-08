from pydantic import BaseModel


class TravelRequest(BaseModel):
    origin: str | None = None
    destination: str | None = None
    trip_duration: int | None = None
    travel_dates: dict | None = None
    travelers: int | None = None
    budget: str | None = None
