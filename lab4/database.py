import os
from datetime import date, timedelta

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_db_engine() -> AsyncEngine:
    url = URL.create(
        "postgresql+asyncpg",
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "12345"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "flights_lab"),
    )
    return create_async_engine(url)


async def load_flights(engine: AsyncEngine, search_date: date):
    query = text("""
        SELECT *
        FROM flights
        WHERE departure_time >= :start
          AND departure_time < :end
    """)

    async with engine.connect() as connection:
        result = await connection.execute(
            query,
            {
                "start": search_date,
                "end": search_date + timedelta(days=1),
            },
        )
        return [dict(row) for row in result.mappings()]