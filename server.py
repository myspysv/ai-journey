import os
import asyncio
import time
import json
import httpx
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from openai import AsyncOpenAI, AuthenticationError, RateLimitError, APIConnectionError

load_dotenv()

chat_histories: dict[str, list[dict[str, str]]] = {}

SYSTEM_PROMPT = (
    "Ти - суворий, але справедливий АІ-ментор із Python та бекенду. "
    "Відповідай чітко, по суті та українською мовою."
)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Помилка: OPENAI_API_KEY не знайдено у файлі .env!")

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

app = FastAPI(title="My First AI Microservice")

class AIRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=2000)
    system_prompt: str = "You are a helpful AI assistant."
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class PromptRequest(BaseModel):
    prompt: str
    temperature: float = 0.7

class TextRequest(BaseModel):
    text: str
    author: str = "Anonymous"

class PromptConfig(BaseModel):
    prompt: str = Field(min_length=5, max_length=500)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=256, ge=10, le=4096)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o"
    messages: list[ChatMessage]

class TranslateRequest(BaseModel):
    text: str
    target_language: str = "English"

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, examples=["alex_1"])
    message: str = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class RawRequest(BaseModel):
    text: str = Field(min_length=5)

class FeedbackAnalysis(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    urgency_score: int = Field(ge=1, le=10)
    main_issue: str
    suggested_reply: str

class VacancyInfo(BaseModel):
    job_title: str
    company: str | None = None
    salary_usd: int | None = None
    is_remote: bool
    skills: list[str]

class ActionItem(BaseModel):
    task: str
    assignee: str | None = None

class MeetingNotes(BaseModel):
    summary: str
    action_items: list[ActionItem]

ANALYZE_SYSTEM_PROMPT = """
Ти — система аналізу відгуків клієнтів. Проаналізуй текст користувача та поверни відповідь СУВОРО у форматі JSON.
JSON має містити рівно 4 поля:
- "sentiment": одне зі значень "positive", "negative" або "neutral"
- "urgency_score": ціле число від 1 до 10 (де 10 — критична проблема, клієнт у люті)
- "main_issue": короткий опис головної проблеми або теми (1 речення українською)
- "suggested_reply": ввічлива та професійна відповідь служби підтримки (1-2 речення українською)
"""   

PARSE_VACANCY_PROMPT = """
Ти — бот-агрегатор вакансій, який читає хаотичні пости з Telegram-каналів і складає їх у базу даних. Проаналізуй текст користувача та поверни відповідь СУВОРО у форматі JSON.
JSON має містити рівно 5 полів:
- "job_title": назва посади
- "company": назва компанії або null, якщо не вказана
- "salary_usd": число в доларах або null, якщо не вказано
- "is_remote": true чи false
- "skills": список технологій, напр. ["Python", "FastAPI", "SQL"]
"""

EXTRACT_TASKS_PROMPT = """
Ти - бот, який читає текст зустрічі та витягує список задач. Проаналізуй текст користувача та поверни відповідь СУВОРО у форматі JSON.
JSON має містити рівно 2 поля:
- "summary": короткий зміст зустрічі
- "action_items": повертає масив з конкретних task (задача) та assignee (хто відповідальний), якщо невідомий assignee - впиши туди null
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": "Отримує поточну ціну криптовалюти в доларах США (USD). Використовуй це, коли користувач питає про вартість або курс криптовалюти.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin": {
                        "type": "string",
                        "description": "ID криптовалюти англійською в нижньому регістрі, наприклад: 'bitcoin', 'ethereum', 'solana'"
                    }
                },
                "required": ["coin"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_currency_rate",
            "description": "Отримує поточний курс іноземної валюти до гривні (UAH) з НБУ. Використовуй це, коли користувач питає про вартість або курс валюти.",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency_code": {
                        "type": "string",
                        "description": "ID валюти англійською в верхньому регістрі, наприклад: 'USD', 'EUR', 'PLN'"
                    }
                },
                "required": ["currency_code"]
            }
        }
    },
    {
            "type": "function",
            "function": {
                "name": "save_price_alert",
                "description": "Зберігає текстове нагадування або нотатку в пам'ять сервера. Використовуй це, коли користувач просить щось запам'ятати, записати або зберегти нагадування.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "note": {
                            "type": "string",
                            "description": "Текст нагадування, який потрібно зберегти (наприклад: 'Ціна Ethereum: $3200')"
                        }
                    },
                    "required": ["note"]
                }
            }
        }
]

students_db = [
    {"id": 1, "name": "Alex", "score": 95},
    {"id": 2, "name": "Maria", "score": 82},
    {"id": 3, "name": "Ivan", "score": 68}
]

saved_alerts: list[str] = []

async def save_price_alert(note: str) -> str:
    saved_alerts.append(note)
    return json.dumps({"status": "saved", "total_alerts": len(saved_alerts)})

def get_trimmed_history(history: list[dict[str, str]], max_recent: int = 6) -> list[dict[str, str]]:
    if len(history) <= max_recent + 1:
        return history
    else:
        return [history[0]] + history[-max_recent:]

async def get_currency_rate(currency_code: str) -> str:
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        response = await http_client.get(url)
        if response.status_code != 200:
            return json.dumps({"error": f"API повернуло статус {response.status_code}"})

        data = response.json()
        target_code = currency_code.upper()

        for item in data:
            if item.get("cc") == target_code:
                return json.dumps({
                    "currency": target_code,
                    "rate_uah": item.get("rate"),
                    "date": item.get("exchangedate")
                })

        return json.dumps({"error": f"Валюту '{currency_code}' не знайдено"})
    
async def get_crypto_price(coin: str) -> str:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin.lower(), "vs_currencies": "usd"}

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        response = await http_client.get(url, params=params)
        if response.status_code != 200:
            return json.dumps({"error": f"API повернуло статус {response.status_code}"})

        data = response.json()
        if coin.lower() not in data:
            return json.dumps({"error": f"Монету '{coin}' не знайдено"})

        price = data[coin.lower()]["usd"]
        return json.dumps({"coin": coin, "price_usd": price})

AVAILABLE_TOOLS = {
    "get_crypto_price": get_crypto_price,
    "get_currency_rate": get_currency_rate,
    "save_price_alert": save_price_alert
}

@app.post("/ask-agent")
async def ask_agent(request: AIRequest):
    messages = [
        {"role": "system", "content": "Ти — корисний фінансовий AI-асистент. Відповідай українською."},
        {"role": "user", "content": request.prompt}
    ]

    try:
        max_steps = 5
        used_tools = []
        
        for step in range(max_steps):
            response = await client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=messages,
                tools=tools,
            )
            assistant_msg = response.choices[0].message

            if not assistant_msg.tool_calls:
                return {
                    "answer": assistant_msg.content,
                    "used_tools": used_tools,
                    "steps": step + 1
                }
                
            messages.append(assistant_msg)
            for tool_call in assistant_msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                if func_name in AVAILABLE_TOOLS:
                    tool_result = await AVAILABLE_TOOLS[func_name](**func_args)
                else:
                    tool_result = json.dumps({"error": "Невідомий інструмент"})
                used_tools.append(func_name)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
        raise HTTPException(status_code=500, detail="Агент перевищив ліміт кроків")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")
        
@app.post("/extract-tasks", response_model=MeetingNotes)
async def extract_tasks(request: RawRequest):
    try:
        completion = await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": EXTRACT_TASKS_PROMPT},
                {"role": "user", "content": request.text}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        raw_json=completion.choices[0].message.content
        extract = MeetingNotes.model_validate_json(raw_json)
        return extract

    except ValidationError as ve:
        raise HTTPException(status_code=502, detail=f"AI повернув некоректну структуру даних: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка серверу: {str(e)}")
    
@app.post("/parse-vacancy", response_model=VacancyInfo)
async def parse_vacancy(request: RawRequest):
    try:
        completion = await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": PARSE_VACANCY_PROMPT},
                {"role": "user", "content": request.text}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        raw_json=completion.choices[0].message.content
        parsed = VacancyInfo.model_validate_json(raw_json)
        return parsed

    except ValidationError as ve:
        raise HTTPException(status_code=502, detail=f"AI повернув некоректну структуру даних: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка серверу: {str(e)}")

@app.post("/analyze", response_model=FeedbackAnalysis)
async def analyze_feedback(request: RawRequest):
    try:
        completion = await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
                {"role": "user", "content": request.text}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        raw_json = completion.choices[0].message.content
        analysis = FeedbackAnalysis.model_validate_json(raw_json)
        return analysis

    except ValidationError as ve:
        raise HTTPException(status_code=502, detail=f"AI повернув некоректну структуру даних: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка серверу: {str(e)}")

@app.post("/chat")
async def chat_with_memory(request: ChatRequest):
    if request.session_id not in chat_histories:
        chat_histories[request.session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    chat_histories[request.session_id].append(
        {"role": "user", "content": request.message}
    )

    try:

        trimmed_messages = get_trimmed_history(chat_histories[request.session_id])

        completion = await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=trimmed_messages,
            temperature=request.temperature,
        )
        reply = completion.choices[0].message.content

        chat_histories[request.session_id].append(
            {"role": "assistant", "content": reply}
        )

        return {
            "session_id": request.session_id,
            "reply": reply,
            "messages_in_history": len(chat_histories[request.session_id])
        }

    except Exception as e:
        chat_histories[request.session_id].pop()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.get("/chat/{session_id}")
def get_chat(session_id: str):
    if not session_id in chat_histories:
        raise HTTPException(status_code=404, detail="Session not found")
    else:
        return {"chat_history": chat_histories.get(session_id)}

@app.delete("/chat/{session_id}")
def delete_chat(session_id: str):
    if not session_id in chat_histories:
        raise HTTPException(status_code=404, detail="Session not found")
    else:
        chat_histories.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}

@app.post("/parallel")
async def parallel(request: AIRequest):
    start = time.perf_counter()

    try:
        res1, res2 = await asyncio.gather(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Поясни тему простими словами, поверни короткий текст (2-3 речення)"},
                    {"role": "user", "content": request.prompt}
                ],
            ),
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Придумай 3 хештега до цієї теми"},
                    {"role": "user", "content": request.prompt}
                ],
            ),
        )
        reply1 = res1.choices[0].message.content
        reply2 = res2.choices[0].message.content
        elapsed = time.perf_counter() - start
        return {
            "reply 1": reply1,
            "reply 2": reply2,
            "elapsed_time": round(elapsed, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Provider Error: {str(e)}")

@app.post("/translate")
async def translate(request: TranslateRequest):
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the user's text into {request.target_language}. Return ONLY the translation, no extra words."},
                {"role": "user", "content": request.text}
            ],
        )
        reply = completion.choices[0].message.content
        return {
            "original": request.text,
            "language": request.target_language,
            "translation": reply
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Provider Error: {str(e)}")

@app.post("/ask-ai")
async def ask_ai(request: AIRequest):
    try:
        completion = await client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.prompt}
            ],
        temperature=request.temperature
        )
        reply = completion.choices[0].message.content
        return {
            "prompt": request.prompt,
            "answer": reply,
            "tokens_used": completion.usage.total_tokens if completion.usage else None
        }

    except AuthenticationError:
        raise HTTPException(status_code=502, detail="Invalid AI API Key")

    except RateLimitError:
        raise HTTPException(status_code=429, detail="AI rate limit exceeded")

    except APIConnectionError:
        raise HTTPException(status_code=503, detail="AI service unreachable")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Provider Error: {str(e)}")

@app.post("/ai/chat")
def ai_chat(body: ChatCompletionRequest):
    if not body.messages:
        last_message = "Список порожній" 
    else:
        last_message = body.messages[-1].content
    return {
        "model": body.model,
        "total_messages": len(body.messages),
        "last_user_message": last_message,
        "reply": "Відповідь згенеровано успішно!"
    }

@app.post("/ai/generate")
def ai_generate(config: PromptConfig):
    return {
        "status": "accepted",
        "config": config
    }


@app.post("/analyze-text")
def analyze_text(request: TextRequest):
    words = request.text.split()
    if not words:
            avg_word_length = 0.0
    else:
        lengths = [len(word.strip(".,!?")) for word in words]
        avg_word_length = round((sum(lengths) / len(words)), 2)
    return {
        "word_count": len(request.text.split()),
        "sentence_count": request.text.count('.') + request.text.count('!') + request.text.count('?'),
        "avg_word_length": avg_word_length,
        "author": request.author
    }

@app.post("/projects/{project_id}/notes")
def analyze_user_text(
        project_id: int,
        note: TextRequest,
        is_pinned: bool = False
):
    return {"project_id": project_id, "is_pinned": is_pinned, "author": note.author, "text": note.text}

@app.get("/alerts")
def get_alerts():
    return {"alerts": saved_alerts}

@app.get("/students")
def get_students(min_score: int = 0):
    return [n["name"] for n in students_db if n["score"] >= min_score]

@app.get("/students/{student_id}")
def find_student(student_id: int):
    for s in students_db:
        if s["id"] == student_id:
            return s["name"]
    return {"error": "Student not found"}

@app.get("/")
def read_root():
    return {"status": "ok", "message": "My first AI backend"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "price": item_id * 10}

@app.get("/health")
def read_health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/users/{username}")
def read_username(username: str):
    return {"username": username, "role": "AI Engineer", "is_active": True}

@app.get("/multiply")
def multiply(a: int, b: int = 2):
    return {"a": a, "b": b, "result": a * b}