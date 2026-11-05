import csv
import random
from datetime import datetime, timedelta

random.seed(42)

start_date = datetime(2026, 11, 4)
airports = [f"A{i:02}" for i in range(1, 31)]

with open("flights.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([
        "carrier", "flight_number", "origin", "destination",
        "departure_time", "arrival_time", "price"
    ])

    for day in range(120):
        for number in range(1500):
            origin, destination = random.sample(airports, 2)
            departure = start_date + timedelta(
                days=day, minutes=random.randint(0, 1439)
            )
            arrival = departure + timedelta(minutes=random.randint(60, 360))
            price = random.randint(2000, 30000)

            writer.writerow([
                "LocalAir", f"LA{number + 1}", origin, destination,
                departure, arrival, price
            ])

print("Создан файл flights.csv: 180000 рейсов")