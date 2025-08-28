# app.py
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import xml.sax.saxutils as saxutils

from niki_bot_core import ask_niki_bot  # your function

app = FastAPI()

# --- CORS: allow your frontend origins during development ---
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    # add your real domain when you deploy the frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # or ["*"] for quick testing
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],             # or ["Content-Type"]
)

@app.get("/")
def read_root():
    return {"message": "Niki Bot is running. Use /ask endpoint with a POST request to talk to the bot."}

# Optional: explicit OPTIONS handler (CORSMiddleware already handles it, but this is safe)
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
        # accept common keys the frontend may send
        for key in ("question", "message", "query", "prompt"):
            if payload.get(key):
                question = payload[key]
                break

    # Fallback: text/plain
    if not question:
        try:
            body_text = await request.body()
            # if Content-Type is text/plain, treat whole body as the question
            if body_text:
                question = body_text.decode("utf-8").strip()
        except Exception:
            pass

    # Fallback: form-encoded (e.g., from simple HTML forms)
    if not question:
        form = await request.form() if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded") else {}
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
