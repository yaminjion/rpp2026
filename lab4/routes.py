from datetime import datetime, timedelta

def find_routes(flights, origin, destination):
    departures = {}

    for flight in flights:
        flight = flight.copy()

        for field in ["departure_time", "arrival_time"]:
            if isinstance(flight[field], str):
                flight[field] = datetime.fromisoformat(flight[field])

        departures.setdefault(flight["origin"], []).append(flight)

    routes = []

    def search(airport, path, visited, total_price):
        if airport == destination:
            routes.append({
                "flights": path,
                "total_price": total_price
            })
            return

        if len(path) == 3:
            return

        for flight in departures.get(airport, []):
            if flight["destination"] in visited:
                continue

            if path:
                waiting = flight["departure_time"] - path[-1]["arrival_time"]

                if not timedelta(hours=1) <= waiting <= timedelta(hours=6):
                    continue

            search(
                flight["destination"],
                path + [flight],
                visited + [flight["destination"]],
                total_price + flight["price"]
            )

    search(origin, [], [origin], 0)

    routes.sort(key=lambda route: route["total_price"])
    return routes[:20]