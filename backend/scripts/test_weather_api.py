import asyncio
from app.tools.weather.open_meteo import get_weather


async def main():
    result = await get_weather(
        latitude=15.3004543, longitude=74.0855134, forecast_days=5
    )

    print("Source:", result["source"])
    print("Timezone:", result["timezone"])

    daily = result["daily"]
    for i, date in enumerate(daily["time"]):
        print(
            {
                "date": date,
                "max_temp": daily["temperature_2m_max"][i],
                "min_temp": daily["temperature_2m_min"][i],
                "precipitation_probability": (
                    daily["precipitation_probability_max"][i]
                ),
                "precipitation_sum": daily["precipitation_sum"][i],
            }
        )


if __name__ == "__main__":
    asyncio.run(main())
