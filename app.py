# app.py
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import xml.sax.saxutils as saxutils

from niki_bot_core import ask_niki_bot  # your function

app = FastAPI()

# --- CORS: allow your frontend origins ---
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://nike-bot.onrender.com",     # <-- your Render static site (PUT YOUR EXACT DOMAIN)
    "https://amnarafi85.github.io",      # <-- GitHub Pages (if you use it)
    # add more origins here if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # use ["*"] temporarily for testing only
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["Content-Type", "Accept"],
)

@app.get("/")
def read_root():
    return {"message": "Niki Bot is running. Use /ask endpoint with a POST request to talk to the bot."}

# Optional: explicit OPTIONS handler (CORSMiddleware already handles it)
@app.options("/ask")
def options_ask():
    return Response(status_code=204)

@app.post("/ask")
async def ask(request: Request):
    """
    Accepts:
      - JSON: {"question": "..."} or {"message": "..."} or {"query": "..."} or {"prompt": "..."}
      - text/plain: raw string
      - application/x-www-form-urlencoded: question=<text>
    Returns: {"answer": "..."}
    """
    # Try JSON first
    payload = None
    try:
        payload = await request.json()
    except Exception:
        payload = None

    question = None
    if isinstance(payload, dict):
        for key in ("question", "message", "query", "prompt"):
            if payload.get(key):
                question = payload[key]
                break

    # Fallback: text/plain
    if not question:
        try:
            body_text = await request.body()
            if body_text:
                question = body_text.decode("utf-8").strip()
        except Exception:
            pass

    # Fallback: form-encoded
    if not question:
        if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            form = await request.form()
            if "question" in form:
                question = form["question"]

    if not question:
        return JSONResponse({"error": "No question provided"}, status_code=400)

    answer = ask_niki_bot(question)
    return {"answer": answer}

@app.post("/whatsapp")
async def whatsapp_reply(Body: str = Form(...)):
    try:
        safe_response = saxutils.escape(ask_niki_bot(Body))
        reply = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_response}</Message>
</Response>"""
        return PlainTextResponse(reply, media_type="application/xml")
    except Exception as e:
        print("Error handling WhatsApp message:", e)
        return PlainTextResponse(
            """<Response><Message>Sorry, an error occurred.</Message></Response>""",
            media_type="application/xml",
        )
