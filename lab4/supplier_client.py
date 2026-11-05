import asyncio
from datetime import date
import httpx

async def load_supplier(
    client: httpx.AsyncClient,
    url: str,
    search_date: date,
):
    for attempt in range(2):
        try:
            response = await client.get(
                url,
                params={"date": search_date.isoformat()},
            )
            response.raise_for_status()
            return response.json()

        except (httpx.HTTPError, ValueError):
            if attempt == 1:
                return None

            await asyncio.sleep(0.2)

    return None
