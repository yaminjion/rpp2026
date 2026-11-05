import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import date

import httpx
from fastapi import FastAPI, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from database import create_db_engine, load_flights
from routes import find_routes
from supplier_client import load_supplier


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_engine = create_db_engine()
    app.state.http_client = httpx.AsyncClient(timeout=None)

    try:
        yield
    finally:
        await app.state.http_client.aclose()
        await app.state.db_engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/search")
async def search(
    request: Request,
    origin: str,
    destination: str,
    date: date,
):
    start = time.perf_counter()
    engine = request.app.state.db_engine
    client = request.app.state.http_client

    async def supplier_request(number: int):
        url = os.getenv(
            f"SUPPLIER_{number}_URL",
            f"http://127.0.0.1:800{number}/flights",
        )

        try:
            async with asyncio.timeout(2):
                supplier_flights = await load_supplier(client, url, date)
            return number, supplier_flights
        except (TimeoutError, httpx.HTTPError, ValueError):
            return number, None

    results = await asyncio.gather(
        load_flights(engine, date),
        supplier_request(1),
        supplier_request(2),
        supplier_request(3),
    )

    flights = results[0]
    unavailable_suppliers = []

    for number, supplier_flights in results[1:]:
        if supplier_flights is None:
            unavailable_suppliers.append(number)
        else:
            flights.extend(supplier_flights)

    if len(unavailable_suppliers) == 3 and not flights:
        raise HTTPException(
            status_code=503,
            detail="Поиск временно недоступен",
        )

    routes = await run_in_threadpool(
        find_routes, flights, origin, destination
    )

    return {
        "routes": routes,
        "unavailable_suppliers": unavailable_suppliers,
        "processing_time_seconds": round(
            time.perf_counter() - start, 3
        ),
    }