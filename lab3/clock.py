from datetime import datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    """Интерфейс часов приложения."""

    def now(self) -> datetime:
        ...


class ClockTimeReversal(Exception):
    """Исключение при попытке перевести часы назад."""

    pass


class SystemClock:
    """Системные часы со сдвигом времени."""

    def __init__(self):
        self._offset = timedelta(0)
        self._last_time = datetime.now()

    def now(self) -> datetime:
        current_time = datetime.now() + self._offset

        if current_time < self._last_time:
            current_time = self._last_time

        self._last_time = current_time
        return current_time

    def set_time(self, target_time: datetime) -> datetime:
        """Устанавливает время приложения через изменение сдвига."""

        current_time = self.now()

        if target_time < current_time:
            raise ClockTimeReversal(
                "Перевод часов приложения назад не допускается"
            )

        self._offset = target_time - datetime.now()
        self._last_time = target_time

        return target_time