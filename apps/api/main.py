"""
FastAPI application entrypoint.
Serves both the JSON API (/auth, /predict, /history) and the
browser-facing pages (/login, /dashboard, /reading/{id}).
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import requests

from apps.api.auth.routes import router as auth_router
from apps.api.routes.predict import router as predict_router
from apps.api.routes.history import router as history_router
from apps.web.routes import router as web_router

app = FastAPI(title="Diagnostic Maintenance Platform API")

# --- JSON API routes ---
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(history_router)

# --- Browser page routes ---
app.include_router(web_router)

# --- Static files (CSS) for the web pages ---
_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")

@app.on_event("startup")
def warmup_ollama():
    try:
        requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2", "prompt": "warm up", "stream": False},
            timeout=90
        )
        print("Ollama model warmed up successfully.")
    except Exception as e:
        print(f"Ollama warmup failed (non-critical): {e}")