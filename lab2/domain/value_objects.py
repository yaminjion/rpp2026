from dataclasses import dataclass

from .exceptions import InvalidValueObject


@dataclass(frozen=True)
class ScooterId:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidValueObject(
                "ID самоката должен быть положительным"
            )


@dataclass(frozen=True)
class UserId:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidValueObject(
                "ID пользователя должен быть положительным"
            )


@dataclass(frozen=True)
class BatteryLevel:
    value: int

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise InvalidValueObject(
                "Уровень заряда должен быть от 0 до 100 процентов"
            )


@dataclass(frozen=True)
class TripCost:
    amount: float

    def __post_init__(self):
        if self.amount < 0:
            raise InvalidValueObject(
                "Стоимость поездки не может быть отрицательной"
            )