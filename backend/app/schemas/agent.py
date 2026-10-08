from typing import Literal

from pydantic import BaseModel, Field


class SupervisorDecision(BaseModel):
    next_agent: Literal[
        "flight", "hotel", "weather", "location", "itinerary", "final"
    ] = Field(description="The next specialist agent that should handle the request")

    reason: str = Field(description="Short explanation for why this agent was selected")
