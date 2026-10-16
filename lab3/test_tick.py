
from datetime import date, timedelta

from app import create_app


app = create_app()
client = app.test_client()

today = date.today()

# Создаём выдачу со сроком возврата вчера.
response = client.post(
    "/loans",
    json={
        "loan_id": 901,
        "book_id": 902,
        "reader_id": 903,
        "issue_date": (today - timedelta(days=10)).isoformat(),
        "due_date": (today - timedelta(days=1)).isoformat(),
        "total_copies": 1,
    },
)

assert response.status_code == 201, response.get_json()
print("Создание выдачи: OK")

# Выдаём книгу, чтобы стало доступно событие просрочки.
response = client.post("/loans/901/issue")

assert response.status_code == 200, response.get_json()
print("Выдача книги: OK")

# Запускаем обработку временных событий.
response = client.post(
    "/internal/tick",
    json={
        "now": (today + timedelta(days=1)).isoformat() + "T12:00:00"
    },
)

assert response.status_code == 200, response.get_json()
print("Вызов tick: OK")

# Проверяем итоговое состояние.
response = client.get("/loans/901")
data = response.get_json()

print("Состояние после tick:", data["state"])
print("Журнал событий:", data["events"])

assert data["state"] == "Просрочена", (
    f"Ожидалось состояние «Просрочена», получено «{data['state']}»"
)

assert any(
    event["event"] == "due_date_expired"
    for event in data["events"]
), "В журнале отсутствует событие due_date_expired"

print("Автоматическая просрочка через API проверена!")
