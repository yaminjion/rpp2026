import time
import os
from datetime import date
from fastapi import FastAPI, HTTPException

from database import load_flights
from supplier_client import load_supplier
from routes import find_routes

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/search")
def search(origin: str, destination: str, date: date):
    start = time.perf_counter()

    flights = load_flights(date)
    unavailable_suppliers = []

    for number in range(1, 4):
        url = os.getenv(
            f"SUPPLIER_{number}_URL",
            f"http://127.0.0.1:800{number}/flights"
        )
        supplier_flights = load_supplier(url, date)

        if supplier_flights is None:
            unavailable_suppliers.append(number)
        else:
            flights.extend(supplier_flights)

    if len(unavailable_suppliers) == 3 and not flights:
        raise HTTPException(
            status_code=503,
            detail="Поиск временно недоступен"
        )

    routes = find_routes(flights, origin, destination)

    return {
        "routes": routes,
        "unavailable_suppliers": unavailable_suppliers,
        "processing_time_seconds": round(time.perf_counter() - start, 3)
    }
