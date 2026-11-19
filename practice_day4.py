import requests

url = "https://httpbin.org/post"
ai_request = {
    "model": "gpt-4o",
    "prompt": "Поясни НТТР",
    "max_tokens": 150
}

response = requests.post(url, json=ai_request, timeout=10)

if response.status_code == 200:
    data = response.json()["json"]
    print(data)
else:
    print(f"Помилка! Сервер повернув код: {response.status_code}")