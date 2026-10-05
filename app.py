from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
from knowledge_base import PNT_KNOWLEDGE


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
        "lead": session.get("lead", {}),
        "history": session.get("history")[-5:]
    }

    print("SESSION CONTEXT:", session_context)

    prompt = f"""
You are AskPNT, the AI sales assistant for PNT Global.

Your role is to have a natural, helpful conversation with website visitors
and help them understand PNT Global's services.

COMPANY KNOWLEDGE:
{json.dumps(PNT_KNOWLEDGE, ensure_ascii=False, indent=2)}

CONVERSATION MEMORY:
{json.dumps(session_context, ensure_ascii=False, indent=2)}

CURRENT USER MESSAGE:
{user_message}

IMPORTANT RULES:

1. Use the company knowledge to answer questions about PNT Global.
2. Use the conversation memory so the visitor does not have to repeat
   information already provided.
3. Continue the conversation naturally from the previous messages.
3a. Before asking for information, check the conversation memory and
    determine whether the visitor has already provided it.

3b. Treat previous user messages as known information. Do not ask the
    visitor to repeat information that is already available in the
    conversation.

3c. Resolve follow-up references such as "it", "this", "that", "me",
    "my business", "my website", "this service" and "what do you
    recommend?" using the previous conversation.

3d. When the current message is a follow-up to an earlier discussion,
    answer it in the context of that discussion rather than starting
    a new conversation.

3e. If the visitor has already identified a business type, service,
    website, goal or requirement, use that information when making
    recommendations.
4. Never invent PNT Global services, prices, features, clients,
   guarantees or other company information.
5. If the knowledge base does not contain the answer, say that the
   PNT Global team can provide the specific information.
6. Keep responses short, clear and conversational.
7. Do not sound like a generic AI chatbot.
8. Do not aggressively sell.
9. Ask only ONE question at a time when a question is needed.
10. If the visitor is discussing a particular service, remember that
    service and keep the conversation relevant to it.
11. If the visitor clearly wants to be contacted or requests a quotation,
    set lead_capture to true.
12. Do not collect or invent lead information. The Flask application
    handles lead capture.
13. Return ONLY valid JSON. No markdown and no explanation outside JSON.

INTENT OPTIONS:
- greeting
- service_detail
- pricing
- faq
- lead_capture
- unknown

Return exactly:

{{
  "reply": "short natural response",
  "intent": "greeting|service_detail|pricing|faq|lead_capture|unknown",
  "lead_capture": false,
  "next_question": null
}}

For next_question:
- Return null if no follow-up is needed.
- Otherwise return a short internal label such as:
  "service"
  "business_type"
  "website"
  "requirement"
  "budget"
  "name"
  "contact"
"""

    text = call_ai(prompt)

    if not text:
        return {
            "reply": "AI service temporarily unavailable.",
            "intent": "unknown",
            "lead_capture": False,
            "next_question": None
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
