import asyncio
import os
import random
from datetime import date, datetime, timedelta

from fastapi import FastAPI, HTTPException

app = FastAPI()

supplier_id = os.getenv("SUPPLIER_ID", "1")
delay_ms = float(os.getenv("DELAY_MS", "300"))
error_percent = float(os.getenv("ERROR_PERCENT", "5"))
slow_percent = float(os.getenv("SLOW_PERCENT", "0"))
flights_count = int(os.getenv("FLIGHTS_COUNT", "500"))

airports = [f"A{i:02}" for i in range(1, 31)]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/flights")
async def flights(date: date):
    delay = random.uniform(delay_ms * 0.7, delay_ms * 1.3) / 1000

    if random.random() < slow_percent / 100:
        delay = 3

    await asyncio.sleep(delay)

    if random.random() < error_percent / 100:
        raise HTTPException(status_code=500, detail="Ошибка поставщика")

    rng = random.Random(f"{supplier_id}:{date}")
    start = datetime.combine(date, datetime.min.time())
    result = []

    for number in range(flights_count):
        origin, destination = rng.sample(airports, 2)
        departure = start + timedelta(minutes=rng.randint(0, 1439))
        arrival = departure + timedelta(minutes=rng.randint(60, 360))
        price = rng.randint(2000, 30000)

        result.append({
            "carrier": f"Supplier {supplier_id}",
            "flight_number": f"S{supplier_id}-{number + 1}",
            "origin": origin,
            "destination": destination,
            "departure_time": departure,
            "arrival_time": arrival,
            "price": price
        })

    return result