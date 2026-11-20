from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str
    temperature: float = 0.7

students_db = [
    {"id": 1, "name": "Alex", "score": 95},
    {"id": 2, "name": "Maria", "score": 82},
    {"id": 3, "name": "Ivan", "score": 68}
]

@app.post("/chat")
def fake_ai_chat(request: PromptRequest):
    return {
        "user_prompt": request.prompt,
        "used_temperature": request.temperature,
        "ai_reply": f"Я отримав твій запит '{request.prompt}' і думаю..."
    }

@app.get("/students")
def get_students(min_score: int = 0):
    return {n["name"] for n in students_db if n["score"] >= min_score}

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