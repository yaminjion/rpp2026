from datetime import datetime
from enum import Enum

from .exceptions import DomainInvariantViolation
from .value_objects import (
    ScooterId,
    UserId,
    BatteryLevel,
    TripCost,
)


class ScooterStatus(Enum):
    FREE = "свободен"
    RENTED = "арендован"
    SERVICE = "на обслуживании"


class Scooter:
    """Агрегат Scooter."""

    MIN_BATTERY_LEVEL = 20

    def __init__(
        self,
        scooter_id: ScooterId,
        battery_level: BatteryLevel,
        status: ScooterStatus = ScooterStatus.FREE,
    ):
        self._scooter_id = scooter_id
        self._battery_level = battery_level
        self._status = status

    @property
    def scooter_id(self):
        return self._scooter_id

    @property
    def battery_level(self):
        return self._battery_level

    @property
    def status(self):
        return self._status

    def start_rental(self):
        """Перевести самокат в состояние аренды."""

        if self._status != ScooterStatus.FREE:
            raise DomainInvariantViolation(
                "Самокат нельзя арендовать: он уже занят или находится на обслуживании"
            )

        if self._battery_level.value < self.MIN_BATTERY_LEVEL:
            raise DomainInvariantViolation(
                "Самокат нельзя арендовать: недостаточный уровень заряда"
            )

        self._status = ScooterStatus.RENTED

    def finish_rental(self):
        """Освободить самокат после завершения поездки."""

        if self._status != ScooterStatus.RENTED:
            raise DomainInvariantViolation(
                "Нельзя завершить аренду: самокат не находится в аренде"
            )

        self._status = ScooterStatus.FREE

    def send_to_service(self):
        """Передать самокат на обслуживание."""

        if self._status == ScooterStatus.RENTED:
            raise DomainInvariantViolation(
                "Нельзя отправить на обслуживание арендованный самокат"
            )

        self._status = ScooterStatus.SERVICE

    def return_from_service(self):
        """Вернуть самокат из обслуживания."""

        if self._status != ScooterStatus.SERVICE:
            raise DomainInvariantViolation(
                "Самокат не находится на обслуживании"
            )

        self._status = ScooterStatus.FREE


class Trip:
    """Агрегат Trip — конкретная поездка пользователя."""

    TARIFF_PER_MINUTE = 10

    def __init__(
        self,
        trip_id: int,
        user_id: UserId,
        scooter_id: ScooterId,
        start_time: datetime,
    ):
        self._trip_id = trip_id
        self._user_id = user_id
        self._scooter_id = scooter_id
        self._start_time = start_time
        self._end_time = None
        self._cost = TripCost(0)

    @property
    def trip_id(self):
        return self._trip_id

    @property
    def user_id(self):
        return self._user_id

    @property
    def scooter_id(self):
        return self._scooter_id

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def cost(self):
        return self._cost

    def finish(self, end_time: datetime):
        """Завершить поездку и рассчитать стоимость."""

        if self._end_time is not None:
            raise DomainInvariantViolation(
                "Поездку нельзя завершить дважды"
            )

        if end_time < self._start_time:
            raise DomainInvariantViolation(
                "Время окончания не может быть раньше времени начала"
            )

        self._end_time = end_time

        duration_seconds = (
            self._end_time - self._start_time
        ).total_seconds()

        duration_minutes = max(
            1,
            int((duration_seconds + 59) // 60),
        )

        total_cost = duration_minutes * self.TARIFF_PER_MINUTE

        self._cost = TripCost(total_cost)