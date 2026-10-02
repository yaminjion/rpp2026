from typing import Protocol

from .entities import Scooter, Trip
from .value_objects import ScooterId, UserId


class ScooterRepository(Protocol):
    """Интерфейс репозитория самокатов."""

    def get(self, scooter_id: ScooterId) -> Scooter | None:
        ...

    def save(self, scooter: Scooter) -> None:
        ...


class TripRepository(Protocol):
    """Интерфейс репозитория поездок."""

    def get(self, trip_id: int) -> Trip | None:
        ...

    def save(self, trip: Trip) -> None:
        ...

    def find_active_by_scooter(
        self,
        scooter_id: ScooterId,
    ) -> Trip | None:
        ...

    def find_active_by_user(
        self,
        user_id: UserId,
    ) -> Trip | None:
        ...