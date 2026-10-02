from domain.entities import Scooter, Trip
from domain.value_objects import ScooterId, UserId


class InMemoryScooterRepository:
    """In-memory реализация репозитория самокатов."""

    def __init__(self):
        self._scooters: dict[int, Scooter] = {}

    def get(self, scooter_id: ScooterId) -> Scooter | None:
        return self._scooters.get(scooter_id.value)

    def save(self, scooter: Scooter) -> None:
        self._scooters[scooter.scooter_id.value] = scooter


class InMemoryTripRepository:
    """In-memory реализация репозитория поездок."""

    def __init__(self):
        self._trips: dict[int, Trip] = {}

    def get(self, trip_id: int) -> Trip | None:
        return self._trips.get(trip_id)

    def save(self, trip: Trip) -> None:
        self._trips[trip.trip_id] = trip

    def find_active_by_scooter(
        self,
        scooter_id: ScooterId,
    ) -> Trip | None:

        for trip in self._trips.values():
            if (
                trip.scooter_id == scooter_id
                and trip.end_time is None
            ):
                return trip

        return None

    def find_active_by_user(
        self,
        user_id: UserId,
    ) -> Trip | None:

        for trip in self._trips.values():
            if (
                trip.user_id == user_id
                and trip.end_time is None
            ):
                return trip

        return None