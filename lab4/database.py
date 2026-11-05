from datetime import date, timedelta
import os
from sqlalchemy import create_engine, text, URL

url = URL.create(
    "postgresql+psycopg",
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "12345"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("POSTGRES_DB", "flights_lab")
)

engine = create_engine(url)


def load_flights(search_date):
    query = text("""
        SELECT *
        FROM flights
        WHERE departure_time >= :start
          AND departure_time < :end
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {
                "start": search_date,
                "end": search_date + timedelta(days=1)
            }
        )
        return [dict(row) for row in result.mappings()]


if __name__ == "__main__":
    flights = load_flights(date(2026, 11, 4))
    print("Количество рейсов:", len(flights))
