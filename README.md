# AI Microservice with FastAPI

A lightweight Python backend microservice built with **FastAPI** and **Pydantic** that integrates with Large Language Models (OpenAI / OpenRouter) to process user prompts and perform text tasks.

## Tech Stack
- Python 3.10+
- FastAPI & Uvicorn
- Pydantic (data validation)
- OpenAI Python SDK
- python-dotenv

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-project-folder>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory and add your API key:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the Server

Start the development server:
```bash
fastapi dev server.py
```

Open your browser at `http://127.0.0.1:8000/docs` to access the interactive Swagger UI documentation.

## Example API Request

**POST** `/ask-ai`
```json
{
  "prompt": "Explain pointers in C in two sentences."
}
```