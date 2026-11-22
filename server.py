from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

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

students_db = [
    {"id": 1, "name": "Alex", "score": 95},
    {"id": 2, "name": "Maria", "score": 82},
    {"id": 3, "name": "Ivan", "score": 68}
]

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

@app.post("/chat")
def fake_ai_chat(request: PromptRequest):
    return {
        "user_prompt": request.prompt,
        "used_temperature": request.temperature,
        "ai_reply": f"Я отримав твій запит '{request.prompt}' і думаю..."
    }

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