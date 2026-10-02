import unittest
from datetime import datetime

from domain.entities import Scooter, Trip, ScooterStatus
from domain.exceptions import (
    DomainInvariantViolation,
    InvalidValueObject,
)
from domain.services import ScooterRentalService
from domain.value_objects import (
    ScooterId,
    UserId,
    BatteryLevel,
    TripCost,
)
from infrastructure.repositories import (
    InMemoryScooterRepository,
    InMemoryTripRepository,
)


class TestScooters(unittest.TestCase):

    def setUp(self):
        self.scooter_repository = InMemoryScooterRepository()
        self.trip_repository = InMemoryTripRepository()

        self.scooter = Scooter(
            scooter_id=ScooterId(1),
            battery_level=BatteryLevel(80),
        )

        self.scooter_repository.save(self.scooter)

        self.service = ScooterRentalService(
            scooter_repository=self.scooter_repository,
            trip_repository=self.trip_repository,
        )

    # 1. ID самоката должен быть положительным
    def test_scooter_id_validation(self):
        with self.assertRaises(InvalidValueObject):
            ScooterId(0)

    # 2. ID пользователя должен быть положительным
    def test_user_id_validation(self):
        with self.assertRaises(InvalidValueObject):
            UserId(-1)

    # 3. Заряд должен находиться от 0 до 100
    def test_battery_validation(self):
        with self.assertRaises(InvalidValueObject):
            BatteryLevel(101)

    # 4. Стоимость не может быть отрицательной
    def test_trip_cost_validation(self):
        with self.assertRaises(InvalidValueObject):
            TripCost(-100)

    # 5. Самокат можно перевести в аренду
    def test_scooter_start_rental(self):
        self.scooter.start_rental()

        self.assertEqual(
            self.scooter.status,
            ScooterStatus.RENTED,
        )

    # 6. Нельзя арендовать самокат с низким зарядом
    def test_cannot_rent_low_battery_scooter(self):
        scooter = Scooter(
            scooter_id=ScooterId(2),
            battery_level=BatteryLevel(10),
        )

        with self.assertRaises(DomainInvariantViolation):
            scooter.start_rental()

    # 7. Нельзя завершить поездку раньше её начала
    def test_cannot_finish_trip_before_start(self):
        trip = Trip(
            trip_id=1,
            user_id=UserId(10),
            scooter_id=ScooterId(1),
            start_time=datetime(2026, 10, 2, 14, 0),
        )

        with self.assertRaises(DomainInvariantViolation):
            trip.finish(
                datetime(2026, 10, 2, 13, 50)
            )

    # 8. Нельзя завершить поездку дважды
    def test_cannot_finish_trip_twice(self):
        trip = Trip(
            trip_id=1,
            user_id=UserId(10),
            scooter_id=ScooterId(1),
            start_time=datetime(2026, 10, 2, 14, 0),
        )

        trip.finish(
            datetime(2026, 10, 2, 14, 10)
        )

        with self.assertRaises(DomainInvariantViolation):
            trip.finish(
                datetime(2026, 10, 2, 14, 20)
            )

    # 9. Стоимость рассчитывается по длительности поездки
    def test_trip_cost_calculation(self):
        trip = Trip(
            trip_id=1,
            user_id=UserId(10),
            scooter_id=ScooterId(1),
            start_time=datetime(2026, 10, 2, 14, 0),
        )

        trip.finish(
            datetime(2026, 10, 2, 14, 15)
        )

        self.assertEqual(
            trip.cost.amount,
            150,
        )

    # 10. Сервис позволяет начать поездку
    def test_service_start_trip(self):
        trip = self.service.start_trip(
            scooter_id=ScooterId(1),
            user_id=UserId(10),
            start_time=datetime(2026, 10, 2, 14, 0),
        )

        self.assertEqual(
            trip.scooter_id,
            ScooterId(1),
        )

        self.assertEqual(
            self.scooter.status,
            ScooterStatus.RENTED,
        )

    # 11. Сервис позволяет завершить поездку
    def test_service_finish_trip(self):
        self.service.start_trip(
            scooter_id=ScooterId(1),
            user_id=UserId(10),
            start_time=datetime(2026, 10, 2, 14, 0),
        )

        trip = self.service.finish_trip(
            scooter_id=ScooterId(1),
            end_time=datetime(2026, 10, 2, 14, 20),
        )

        self.assertEqual(
            trip.cost.amount,
            200,
        )

        self.assertEqual(
            self.scooter.status,
            ScooterStatus.FREE,
        )

    # 12. Нельзя начать вторую поездку на занятом самокате
    def test_cannot_start_second_trip(self):
        self.service.start_trip(
            scooter_id=ScooterId(1),
            user_id=UserId(10),
            start_time=datetime(2026, 10, 2, 14, 0),
        )

        with self.assertRaises(DomainInvariantViolation):
            self.service.start_trip(
                scooter_id=ScooterId(1),
                user_id=UserId(20),
                start_time=datetime(2026, 10, 2, 14, 5),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)