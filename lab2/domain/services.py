from datetime import datetime

from .entities import Trip
from .exceptions import DomainInvariantViolation
from .repositories import ScooterRepository, TripRepository
from .value_objects import ScooterId, UserId


class ScooterRentalService:
    """Доменный сервис проката самокатов."""

    def __init__(
        self,
        scooter_repository: ScooterRepository,
        trip_repository: TripRepository,
    ):
        self._scooter_repository = scooter_repository
        self._trip_repository = trip_repository

    def start_trip(
        self,
        scooter_id: ScooterId,
        user_id: UserId,
        start_time: datetime,
    ) -> Trip:
        """Начать поездку."""

        scooter = self._scooter_repository.get(scooter_id)

        if scooter is None:
            raise DomainInvariantViolation(
                "Самокат не найден"
            )

        active_trip = self._trip_repository.find_active_by_scooter(
            scooter_id
        )

        if active_trip is not None:
            raise DomainInvariantViolation(
                "Самокат уже используется в другой поездке"
            )

        user_trip = self._trip_repository.find_active_by_user(
            user_id
        )

        if user_trip is not None:
            raise DomainInvariantViolation(
                "У пользователя уже есть активная поездка"
            )

        scooter.start_rental()

        trip_id = self._generate_trip_id()

        trip = Trip(
            trip_id=trip_id,
            user_id=user_id,
            scooter_id=scooter_id,
            start_time=start_time,
        )

        self._scooter_repository.save(scooter)
        self._trip_repository.save(trip)

        return trip

    def finish_trip(
        self,
        scooter_id: ScooterId,
        end_time: datetime,
    ) -> Trip:
        """Завершить поездку."""

        scooter = self._scooter_repository.get(scooter_id)

        if scooter is None:
            raise DomainInvariantViolation(
                "Самокат не найден"
            )

        trip = self._trip_repository.find_active_by_scooter(
            scooter_id
        )

        if trip is None:
            raise DomainInvariantViolation(
                "Активная поездка для самоката не найдена"
            )

        trip.finish(end_time)
        scooter.finish_rental()

        self._trip_repository.save(trip)
        self._scooter_repository.save(scooter)

        return trip

    def _generate_trip_id(self) -> int:
        """Сгенерировать новый ID поездки."""

        trip_id = 1

        while self._trip_repository.get(trip_id) is not None:
            trip_id += 1

        return trip_id