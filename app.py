from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime


# ----------------------------
# OpenRoute config (NEW SDK)
# ----------------------------

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


import requests
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_ai(prompt):
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://pntglobal.com",  # optional but recommended
                "X-Title": "AskPNT"
            },
            json={
                "model": "openai/gpt-4o-mini",  # safe + stable free/cheap model
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=30
        )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("OPENROUTER ERROR:", e)
        return "AI service temporarily unavailable."
# ----------------------------
# Flask app
# ----------------------------
app = Flask(__name__)
CORS(app)

# ----------------------------
# In-memory session store
# ----------------------------
sessions = {}

def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            "lead_stage": None,
            "service": None,
            "history": [],
            "last_question": None,
            "lead": {},
            "created_at": str(datetime.now())
        }
    return sessions[session_id]

# ----------------------------
# Safe JSON extractor
# ----------------------------
def extract_json(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start != -1 and end != -1:
            return json.loads(text[start:end])
    except Exception as e:
        print("JSON PARSE ERROR:", e)

    return {
        "reply": text,
        "intent": "unknown",
        "lead_capture": False,
        "next_question": None
    }

# ----------------------------
# AI agent reply
# ----------------------------
def ai_agent_reply(user_message, session):

    session_context = {
        "lead_stage": session.get("lead_stage"),
        "service": session.get("service"),
        "last_question": session.get("last_question"),
        "history": session.get("history")[-5:]
    }

    print("SESSION CONTEXT:", session_context)

    prompt = f"""
You are a smart PNT Global sales assistant.

User message:
{user_message}

Context:
{json.dumps(session_context)}

Return ONLY valid JSON:
{{
  "reply": "short response",
  "intent": "greeting|service_detail|pricing|faq|lead_capture|unknown",
  "lead_capture": false,
  "next_question": null
}}
"""

    text = call_ai(prompt)

    if not text:
        return {
            "reply": "AI service temporarily unavailable.",
            "intent": "unknown",
            "lead_capture": False,
            "next_question": None
        }

    print("GEMINI RAW:", text)

    return extract_json(text)

# ----------------------------
# Chat endpoint
# ----------------------------
@app.route("/agent-chat", methods=["POST"])
def chat():

    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not msg:
        return jsonify({"reply": "Please send a message."})

    session = get_session(session_id)
    response = ai_agent_reply(msg, session)

    # update session tracking
    session["last_question"] = response.get("next_question")

    if response.get("lead_capture"):
        session["lead_stage"] = "capture"

    # lead flow
    if session["lead_stage"] == "capture":

        if "name" not in session["lead"]:
            session["lead"]["name"] = msg
            response["reply"] += " 👍 Can you share your email or WhatsApp number?"
            session["last_question"] = "lead_contact"

        elif "contact" not in session["lead"] and session.get("last_question") == "lead_contact":
            session["lead"]["contact"] = msg
            session["lead_stage"] = "complete"
            session["last_question"] = None
            response["reply"] = "Perfect 👍 Our team will contact you shortly."

    session["history"].append({
        "user": msg,
        "bot": response["reply"],
        "time": str(datetime.now())
    })

    response["session_id"] = session_id

    return jsonify(response)

# ----------------------------
# Health check
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "AskPNT AI vNext Running 🚀"

# ----------------------------
# Run (local only)
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
