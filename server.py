import os
import asyncio
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
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

students_db = [
    {"id": 1, "name": "Alex", "score": 95},
    {"id": 2, "name": "Maria", "score": 82},
    {"id": 3, "name": "Ivan", "score": 68}
]

def get_trimmed_history(history: list[dict[str, str]], max_recent: int = 6) -> list[dict[str, str]]:
    if len(history) <= max_recent + 1:
        return history
    else:
        return [history[0]] + history[-max_recent:]

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


@app.post("/analyze")
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