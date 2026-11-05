import time
import requests
from datetime import date


def load_supplier(url, search_date):
    deadline = time.monotonic() + 2

    for attempt in range(2):
        remaining = deadline - time.monotonic()

        if remaining <= 0:
            return None

        try:
            response = requests.get(
                url,
                params={"date": search_date.isoformat()},
                timeout=remaining
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException:
            if attempt == 1:
                return None

            if deadline - time.monotonic() <= 0.2:
                return None

            time.sleep(0.2)


if __name__ == "__main__":
    flights = load_supplier(
        "http://127.0.0.1:8001/flights",
        date(2026, 11, 4)
    )

    if flights is None:
        print("Поставщик не ответил")
    else:
        print("Количество рейсов поставщика:", len(flights))