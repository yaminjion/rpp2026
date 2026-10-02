from datetime import datetime

from domain.entities import Scooter, ScooterStatus
from domain.services import ScooterRentalService
from domain.value_objects import (
    ScooterId,
    UserId,
    BatteryLevel,
)
from infrastructure.repositories import (
    InMemoryScooterRepository,
    InMemoryTripRepository,
)

# СОЗДАНИЕ РЕПОЗИТОРИЕВ

scooter_repository = InMemoryScooterRepository()
trip_repository = InMemoryTripRepository()


# ДОБАВЛЕНИЕ САМОКАТА

scooter = Scooter(
    scooter_id=ScooterId(1),
    battery_level=BatteryLevel(80),
)

scooter_repository.save(scooter)


# СОЗДАНИЕ ДОМЕННОГО СЕРВИСА

service = ScooterRentalService(
    scooter_repository=scooter_repository,
    trip_repository=trip_repository,
)


# НАЧАЛО ПОЕЗДКИ


print("=== НАЧАЛО ПОЕЗДКИ ===")

trip = service.start_trip(
    scooter_id=ScooterId(1),
    user_id=UserId(10),
    start_time=datetime(2026, 10, 2, 14, 0),
)

print("ID поездки:", trip.trip_id)
print("ID пользователя:", trip.user_id)
print("ID самоката:", trip.scooter_id)
print("Время начала:", trip.start_time)
print("Статус самоката:", scooter.status.value)
print("Заряд:", scooter.battery_level.value, "%")


# ЗАВЕРШЕНИЕ ПОЕЗДКИ


print("\n=== ЗАВЕРШЕНИЕ ПОЕЗДКИ ===")

finished_trip = service.finish_trip(
    scooter_id=ScooterId(1),
    end_time=datetime(2026, 10, 2, 14, 15),
)

print("Время окончания:", finished_trip.end_time)
print("Стоимость:", finished_trip.cost.amount, "руб.")
print("Статус самоката:", scooter.status.value)


# ПРОВЕРКА ПОВТОРНОГО ЗАВЕРШЕНИЯ

print("\n=== ПРОВЕРКА ПОВТОРНОГО ЗАВЕРШЕНИЯ ===")

try:
    finished_trip.finish(
        datetime(2026, 10, 2, 14, 20)
    )
except Exception as e:
    print("Ошибка:", e)


# ПРОВЕРКА НЕПРАВИЛЬНОГО ВРЕМЕНИ

print("\n=== ПРОВЕРКА НЕПРАВИЛЬНОГО ВРЕМЕНИ ===")

test_scooter = Scooter(
    scooter_id=ScooterId(2),
    battery_level=BatteryLevel(90),
)

scooter_repository.save(test_scooter)

test_trip = service.start_trip(
    scooter_id=ScooterId(2),
    user_id=UserId(20),
    start_time=datetime(2026, 10, 2, 15, 0),
)

try:
    test_trip.finish(
        datetime(2026, 10, 2, 14, 50)
    )
except Exception as e:
    print("Ошибка:", e)


# ПРОВЕРКА НИЗКОГО ЗАРЯДА

print("\n=== ПРОВЕРКА НИЗКОГО ЗАРЯДА ===")

low_battery_scooter = Scooter(
    scooter_id=ScooterId(3),
    battery_level=BatteryLevel(10),
)

scooter_repository.save(low_battery_scooter)

try:
    service.start_trip(
        scooter_id=ScooterId(3),
        user_id=UserId(30),
        start_time=datetime(2026, 10, 2, 16, 0),
    )
except Exception as e:
    print("Ошибка:", e)


# ПРОВЕРКА ПОВТОРНОЙ АРЕНДЫ

print("\n=== ПРОВЕРКА ПОВТОРНОЙ АРЕНДЫ ===")

busy_scooter = Scooter(
    scooter_id=ScooterId(4),
    battery_level=BatteryLevel(90),
)

scooter_repository.save(busy_scooter)

service.start_trip(
    scooter_id=ScooterId(4),
    user_id=UserId(40),
    start_time=datetime(2026, 10, 2, 17, 0),
)

try:
    service.start_trip(
        scooter_id=ScooterId(4),
        user_id=UserId(50),
        start_time=datetime(2026, 10, 2, 17, 5),
    )
except Exception as e:
    print("Ошибка:", e)