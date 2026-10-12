from pydantic import BaseModel, Field, ConfigDict


class TravelRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    origin: str | None = None
    destination: str | None = None
    trip_duration: int | None = None
    travel_dates: dict | None = None
    travelers: int | None = None
    budget: str | None = None

    # Optional, explicitly supplied cost information.
    hotel_per_person_per_night: float | None = Field(default=None, ge=0)
    food_per_person_per_day: float | None = Field(default=None, ge=0)
    activities_per_person: float | None = Field(default=None, ge=0)
    transport_total: float | None = Field(default=None, ge=0)
