
from app import app


def test_api():
    client = app.test_client()

    # 1. Создаём выдачу книги.
    response = client.post(
        "/loans",
        json={
            "loan_id": 101,
            "book_id": 201,
            "reader_id": 301,
            "issue_date": "2026-10-16",
            "due_date": "2026-10-20",
            "total_copies": 2,
        },
    )

    print("Создание выдачи:", response.status_code)
    print(response.get_json())
    assert response.status_code == 201

    # 2. Получаем текущее состояние.
    response = client.get("/loans/101")

    print("\nПолучение выдачи:", response.status_code)
    print(response.get_json())
    assert response.status_code == 200

    # 3. Выдаём книгу.
    response = client.post("/loans/101/issue")

    print("\nВыдача книги:", response.status_code)
    print(response.get_json())
    assert response.status_code == 200

    # 4. Повторная выдача должна вернуть ошибку перехода.
    response = client.post("/loans/101/issue")

    print("\nПовторная выдача:", response.status_code)
    print(response.get_json())
    assert response.status_code == 409

    # 5. Проверяем служебный маршрут часов.
    response = client.post(
        "/internal/tick",
        json={"now": "2026-10-17T12:00:00"},
    )

    print("\nПеревод часов:", response.status_code)
    print(response.get_json())
    assert response.status_code == 200

    print("\nВсе проверки API пройдены.")


if __name__ == "__main__":
    test_api()
