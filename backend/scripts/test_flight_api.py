import asyncio
from pprint import pprint

from app.tools.flights.aviationstack import search_flights


async def main():
    result = await search_flights(origin="HYD", destination="GOI")

    print("Result count:", result["count"])
    pprint(result["results"][:2])


if __name__ == "__main__":
    asyncio.run(main())
