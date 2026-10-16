from datetime import datetime, timedelta

from clock import SystemClock, ClockTimeReversal


clock = SystemClock()

# Переводим часы приложения вперёд на один день.
future_time = datetime.now() + timedelta(days=1)
clock.set_time(future_time)

print("Время вперёд: OK")

# Пытаемся перевести часы назад.
try:
    clock.set_time(datetime.now() - timedelta(days=1))
    print("ОШИБКА: перевод назад разрешён")
except ClockTimeReversal:
    print("Запрет перевода назад: OK")