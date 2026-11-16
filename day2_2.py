api_response = {
    "id": "chatcmpl-123",
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Привіт! Чим я можу тобі допомогти?"
            }
        }
    ],
    "usage": {"prompt_tokens": 15, "completion_tokens": 25}
}

usage = api_response.get("usage", {})
total_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

choices = api_response.get("choices", [])

if choices:
    content = choices[0].get("message", {}).get("content", "Текст відсутній")
else:
    content = "Відповідь не отримано"

print(content)
print(total_tokens)