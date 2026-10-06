from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
from knowledge_base import PNT_KNOWLEDGE
from agent_rules import ASKPNT_RULES


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
            "business_type": None,
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
        "business_type": session.get("business_type"),
        "last_question": session.get("last_question"),
        "lead": session.get("lead", {}),
        "history": session.get("history")[-5:]
    }

    print("SESSION CONTEXT:", session_context)

    prompt = f"""
You are AskPNT, the AI sales assistant for PNT Global.

Your role is to have a natural, helpful conversation with website visitors
and help them understand PNT Global's services.

COMPANY KNOWLEDGE:
{PNT_KNOWLEDGE}

CONVERSATION MEMORY:
{json.dumps(session_context, ensure_ascii=False, indent=2)}

CURRENT USER MESSAGE:
{user_message}

INTENT OPTIONS:
- greeting
- service_detail
- pricing
- faq
- lead_capture
- unknown

Return ONLY this JSON structure:

{{
  "reply": "short natural response",
  "intent": "greeting|service_detail|pricing|faq|lead_capture|unknown",
  "lead_capture": false,
  "next_question": null,
  "service": null
  "business_type": null
}}

The "service" field should contain the current service being discussed,
for example:
"Shopify"
"SEO"
"WordPress"
"Website Development"
"Software Development"
"AI Solutions"

If no service is currently identified, use null.
"""
The "business_type" field should contain the type of business identified
from the conversation, for example:

"Online Store"
"Textile Manufacturer"
"Restaurant"
"IT Company"
"Export Business"

If no business type is currently identified, use null.

    text = call_ai(prompt)

    if not text:
        return {
            "reply": "AI service temporarily unavailable.",
            "intent": "unknown",
            "lead_capture": False,
            "next_question": None,
            "service": None
            
        }

    print("AI RAW:", text)

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

    # Get AI response
    response = ai_agent_reply(msg, session)

    # ----------------------------
    # Update conversation memory
    # ----------------------------

    session["last_question"] = response.get("next_question")

    # Remember current service
    if response.get("service"):
        session["service"] = response.get("service")

    # Remember business type
    if response.get("business_type"):
        session["business_type"] = response.get("business_type")
    
    # ----------------------------
    # Lead capture
    # ----------------------------

    if response.get("lead_capture"):
        session["lead_stage"] = "capture"

    # ----------------------------
    # Save conversation history
    # ----------------------------

    session["history"].append({
        "user": msg,
        "bot": response.get("reply", ""),
        "time": str(datetime.now())
    })

    # Keep only recent conversation history
    session["history"] = session["history"][-10:]

    # Return session ID to browser
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
