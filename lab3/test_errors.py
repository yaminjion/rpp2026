
from app import create_app


app = create_app()
client = app.test_client()

# Несуществующая выдача должна возвращать 404.
response = client.get("/loans/999999")
print("Несуществующая выдача:", response.status_code, response.get_json())
assert response.status_code == 404

# Недопустимый переход должен возвращать 409.
response = client.post(
    "/loans",
    json={
        "loan_id": 990,
        "book_id": 991,
        "reader_id": 992,
        "issue_date": "2026-10-16",
        "due_date": "2026-10-20",
        "total_copies": 5,
    },
)
assert response.status_code == 201

response = client.post("/loans/990/issue")
assert response.status_code == 200

response = client.post("/loans/990/issue")
print("Недопустимый переход:", response.status_code, response.get_json())
assert response.status_code == 409

# Некорректный формат даты должен возвращать 422.
response = client.post(
    "/loans",
    json={
        "loan_id": 993,
        "book_id": 994,
        "reader_id": 995,
        "issue_date": "не-дата",
        "due_date": "2026-10-20",
        "total_copies": 1,
    },
)
print("Некорректная дата:", response.status_code, response.get_json())
assert response.status_code == 422

print("Проверки ошибок пройдены!")
