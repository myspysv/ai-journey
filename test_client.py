import requests

# Стукаємо у свій GET-маршрут
r1 = requests.get("http://127.0.0.1:8000/students", params={"min_score": 80})
print("Топ студенти:", r1.json())

# Стукаємо у свій POST-маршрут
r2 = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"prompt": "Поясни FastAPI у двох словах", "temperature": 0.2}
)
print("Відповідь мого AI-сервера:", r2.json())