from flask import Flask, request, jsonify
from flask_cors import CORS
import os, uuid, json
from datetime import datetime
import openai
import requests

# ----------------------------
# CONFIG
# ----------------------------
openai.api_key = os.environ.get("OPENAI_API_KEY")

AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")  # openai | ollama
OLLAMA_URL = "http://localhost:11434/api/generate"

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
# OLLAMA CALL
# ----------------------------
def ollama_reply(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        print("OLLAMA ERROR:", e)
        return ""

# ----------------------------
# AI AGENT
# ----------------------------
def ai_agent_reply(user_message, session):

    session_context = {
        "lead_stage": session.get("lead_stage"),
        "service": session.get("service"),
        "last_question": session.get("last_question"),
        "history": session.get("history")
    }

    prompt = f"""
You are a smart PNT Global sales assistant.

User message: {user_message}
Session context: {json.dumps(session_context)}

IMPORTANT RULES:
- Respond ONLY in valid JSON
- JSON format:
  {{
    "reply": "...",
    "intent": "greeting|service_detail|pricing|faq|lead_capture|unknown",
    "lead_capture": true/false,
    "next_question": "optional string"
  }}

Be short, professional, and helpful.
"""

    try:
        # -------------------------
        # OPENAI MODE
        # -------------------------
        if AI_PROVIDER == "openai":
            response = openai.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            content = response.choices[0].message.content

        # -------------------------
        # OLLAMA MODE
        # -------------------------
        else:
            content = ollama_reply(prompt)

        # try parsing JSON safely
        try:
            return json.loads(content)
        except:
            return {
                "reply": content,
                "intent": "unknown",
                "lead_capture": False,
                "next_question": None
            }

    except Exception as e:
        print("AI ERROR:", e)
        return {
            "reply": "Sorry, I couldn't process that right now.",
            "intent": "unknown",
            "lead_capture": False,
            "next_question": None
        }

# ----------------------------
# CHAT ENDPOINT
# ----------------------------
@app.route("/agent-chat", methods=["POST"])
def chat():
    data = request.get_json()

    msg = data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    session = get_session(session_id)
    response = ai_agent_reply(msg, session)

    # update session context
    session["last_question"] = response.get("next_question")

    if response.get("lead_capture"):
        session["lead_stage"] = "capture"

    # lead capture flow
    if session["lead_stage"] == "capture":
        if "name" not in session["lead"]:
            session["lead"]["name"] = msg
            response["reply"] += " Thanks! Can you share your email or WhatsApp number?"
            session["last_question"] = "lead_contact"

        elif "contact" not in session["lead"] and session.get("last_question") == "lead_contact":
            session["lead"]["contact"] = msg
            session["lead_stage"] = "complete"
            session["last_question"] = None
            response["reply"] = "Perfect 👍 Our team will contact you shortly."

    # history log
    session["history"].append({
        "user": msg,
        "bot": response["reply"],
        "time": str(datetime.now())
    })

    response["session_id"] = session_id

    return jsonify(response)

# ----------------------------
# HOME
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "AskPNT AI vNext Running 🚀"

# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
