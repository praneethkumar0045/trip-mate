import re

from app.llm.factory import get_llm
from app.agents.final.prompts import FINAL_RESPONSE_PROMPT

llm = get_llm()


def replace_section(response: str, heading: str, replacement: str) -> str:
    """Replace a Markdown section, including bold-formatted headings."""
    heading_line = r"^[ \t]*(?:\*\*)?#\s+.+?(?:\*\*)?[ \t]*$"

    section_pattern = (
        rf"(?ms)^[ \t]*(?:\*\*)?#\s+{re.escape(heading)}"
        rf"[ \t]*(?:\*\*)?[ \t]*\n"
        rf".*?(?={heading_line}|\Z)"
    )

    replacement_text = f"**# {heading}**\n\n{replacement.strip()}\n\n"

    if re.search(section_pattern, response):
        return re.sub(
            section_pattern,
            lambda _: replacement_text,
            response,
            count=1,
        )

    return response.rstrip() + f"\n\n{replacement_text}"


def validate_flight_section(response: str, flights) -> str:
    if not isinstance(flights, dict):
        return response

    if flights.get("status") == "needs_clarification":
        message = (
            "Flight research is incomplete because travel dates are missing. "
            "No flight options should be treated as confirmed. "
            "Provide the intended departure date to continue."
        )
        return replace_section(response, "Flight Information", message)

    if flights.get("status") == "unavailable":
        message = (
            "Flight research is currently unavailable. "
            "No flight options or fares have been confirmed."
        )
        return replace_section(response, "Flight Information", message)

    return response


def validate_hotel_section(response: str, hotels) -> str:
    if isinstance(hotels, dict):
        status = hotels.get("status")

        if status == "needs_clarification":
            message = hotels.get("message") or (
                "Hotel research requires more trip details before "
                "options can be assessed."
            )
            return replace_section(response, "Hotel Information", str(message))

        if status == "unavailable":
            return replace_section(
                response,
                "Hotel Information",
                "Hotel research is currently unavailable. "
                "No hotel availability or room rates have been confirmed.",
            )

        if status == "success":
            results = hotels.get("results") or []
            if not results:
                return replace_section(
                    response,
                    "Hotel Information",
                    "No hotel options were returned by the research.",
                )

        return response

    # The current hotel agent returns generated text in a list.
    if isinstance(hotels, list):
        text_results = [
            item for item in hotels if isinstance(item, str) and item.strip()
        ]

        if not text_results:
            message = (
                "No verified hotel options were returned. "
                "Travel dates, guest count, and budget may be needed "
                "before hotel research can be completed."
            )
            return replace_section(response, "Hotel Information", message)

        # This format contains a generated report, not structured,
        # independently verified hotel listings.
        combined = "\n".join(text_results).lower()
        missing_details = []

        if "check-in date" in combined or "travel dates" in combined:
            missing_details.append("travel dates")
        if "number of guests" in combined or "travelers" in combined:
            missing_details.append("number of guests")
        if "budget preference" in combined or "budget" in combined:
            missing_details.append("accommodation budget")

        details = ", ".join(missing_details) or "required trip details"
        message = (
            "No verified hotel listings or room rates were returned. "
            f"The hotel research report indicates that {details} "
            "need clarification."
        )
        return replace_section(response, "Hotel Information", message)

    return response


def validate_weather_section(response: str, weather) -> str:
    if not isinstance(weather, dict):
        message = (
            "A usable weather forecast was not retrieved. "
            "Weather conditions for the trip remain unconfirmed."
        )
        return replace_section(response, "Weather Considerations", message)

    if weather.get("status") != "success":
        message = (
            "A live forecast was not successfully retrieved. "
            "Weather conditions for the trip remain unconfirmed."
        )
        return replace_section(response, "Weather Considerations", message)

    forecasts = weather.get("forecasts") or []

    if not forecasts:
        message = "The weather service did not return usable forecast records."
        return replace_section(response, "Weather Considerations", message)

    lines = [
        "The following forecast records were returned by the weather service. "
        "Confirm that these dates match your intended trip before relying on them.",
        "",
    ]

    for forecast in forecasts:
        if not isinstance(forecast, dict):
            continue

        date = forecast.get("date")
        if not date:
            continue

        details = [f"**{date}:**"]

        minimum = forecast.get("min_temp")
        maximum = forecast.get("max_temp")

        if minimum is not None and maximum is not None:
            details.append(f"{minimum}–{maximum}°C")

        probability = forecast.get("precipitation_probability")
        if probability is not None:
            details.append(f"precipitation probability {probability}%")

        precipitation = forecast.get("precipitation_sum")
        if precipitation is not None:
            details.append(f"precipitation {precipitation} mm")

        lines.append(" ".join(details))

    return replace_section(
        response,
        "Weather Considerations",
        "\n".join(lines),
    )


def final_agent(state):
    prompt = FINAL_RESPONSE_PROMPT.format(
        user_query=state.get("user_query", ""),
        origin=state.get("origin"),
        destination=state.get("destination"),
        trip_duration=state.get("trip_duration"),
        travel_dates=state.get("travel_dates"),
        travelers=state.get("travelers"),
        budget=state.get("budget"),
        flight_results=state.get("flight_results") or [],
        hotel_results=state.get("hotel_results") or [],
        weather_results=state.get("weather_results") or {},
        location_results=state.get("location_results") or [],
        itinerary=state.get("itinerary") or {},
    )

    result = llm.invoke(prompt)
    response = result.content

    # Enforce known research statuses after LLM generation.
    response = validate_flight_section(response, state.get("flight_results"))
    response = validate_hotel_section(response, state.get("hotel_results"))
    response = validate_weather_section(response, state.get("weather_results"))

    return {"final_response": response}
