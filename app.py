from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
import xml.sax.saxutils as saxutils  # 👈 required to escape special characters
from niki_bot_core import ask_niki_bot

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Niki Bot is running. Use /ask endpoint with a POST request to talk to the bot."}

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question")
    if not question:
        return {"error": "No question provided"}
    answer = ask_niki_bot(question)
    return {"answer": answer}

@app.post("/whatsapp")
async def whatsapp_reply(Body: str = Form(...)):
    try:
        # Escape special characters like &, <, > in response
        safe_response = saxutils.escape(ask_niki_bot(Body))
        reply = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_response}</Message>
</Response>"""
        return PlainTextResponse(reply, media_type="application/xml")
    except Exception as e:
        print("Error handling WhatsApp message:", e)
        return PlainTextResponse("""<Response><Message>Sorry, an error occurred.</Message></Response>""", media_type="application/xml")
