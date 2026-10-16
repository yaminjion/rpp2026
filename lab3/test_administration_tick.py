
from datetime import date, datetime, timedelta

from app import create_app


app = create_app()
client = app.test_client()

# Берём завтрашнюю дату как базовую, чтобы целевое время
# гарантированно было в будущем относительно текущего момента.
today = date.today()
due_date = today - timedelta(days=31)

response = client.post(
    "/loans",
    json={
        "loan_id": 951,
        "book_id": 952,
        "reader_id": 953,
        "issue_date": (due_date - timedelta(days=10)).isoformat(),
        "due_date": due_date.isoformat(),
        "total_copies": 5,
    },
)
assert response.status_code == 201, response.get_json()

response = client.post("/loans/951/issue")
assert response.status_code == 200, response.get_json()

# Используем текущее время компьютера плюс небольшое смещение.
# Оно должно быть не раньше времени, которое уже видят часы приложения.
target_time = datetime.now() + timedelta(minutes=5)

response = client.post(
    "/internal/tick",
    json={"now": target_time.isoformat()},
)
print("Вызов tick:", response.status_code, response.get_json())
assert response.status_code == 200

response = client.get("/loans/951")
data = response.get_json()

print("Состояние:", data["state"])
print("Журнал событий:", data["events"])

assert data["state"] == "Передана администрации", (
    f"Получено неожиданное состояние: {data['state']}"
)

print("Передача администрации через tick проверена!")
