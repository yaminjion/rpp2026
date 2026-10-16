
import app as app_module

client = app_module.app.test_client()


@app_module.app.get("/test-gateway-error")
def test_gateway_error():
    raise app_module.GatewayUnresolved("Шлюз недоступен")


response = client.get("/test-gateway-error")

print("Статус:", response.status_code)
print("Ответ:", response.get_json())

assert response.status_code == 500
assert response.get_json()["error"] == "gateway_unresolved"
assert "message" in response.get_json()

print("Проверка GatewayUnresolved пройдена!")
