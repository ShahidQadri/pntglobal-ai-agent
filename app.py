from dotenv import load_dotenv
import os, openai

load_dotenv()  # loads .env locally
openai.api_key = os.environ.get("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key not found. Set it in .env")
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, uuid, json, openai
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ----------------------------
# SESSION STORE
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
# AI MODULE
# ----------------------------
def ai_agent_reply(user_message, session):
    """
    Sends user message + session context to GPT and returns structured response.
    """
    session_context = {
        "lead_stage": session.get("lead_stage"),
        "service": session.get("service"),
        "last_question": session.get("last_question"),
        "history": session.get("history")
    }

    prompt = f"""
You are a smart PNT Global sales assistant. 
User said: "{user_message}"
Session context: {json.dumps(session_context)}

Rules:
- Respond as JSON ONLY with:
  - reply: text to send to user
  - intent: one of greeting, service_detail, pricing, faq, lead_capture, unknown
  - lead_capture: true/false
  - next_question: follow-up question to store in session (optional)

- Make replies short, clear, and professional.
- If user shows interest in a service or pricing, set lead_capture=True.
- If user says yes/no, handle naturally based on last_question.
- Never loop on the same question.

JSON format only.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print("AI ERROR:", e)
        return {
            "reply": "Sorry, I didn't understand. Can you rephrase?",
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

    # Update session context
    session["last_question"] = response.get("next_question")
    if response.get("lead_capture"):
        session["lead_stage"] = "capture"
    if session["lead_stage"] == "capture":
        # Capture name/contact automatically if user responds
        if "name" not in session["lead"]:
            session["lead"]["name"] = msg
            response["reply"] += " Thanks! Can you share your email or WhatsApp number?"
            session["last_question"] = "lead_contact"
        elif "contact" not in session["lead"] and session.get("last_question") == "lead_contact":
            session["lead"]["contact"] = msg
            session["lead_stage"] = "complete"
            session["last_question"] = None
            response["reply"] = "Perfect 👍 Our team will contact you shortly."

    # Add to session history
    session["history"].append({"user": msg, "bot": response["reply"], "time": str(datetime.now())})
    response["session_id"] = session_id

    return jsonify(response)

# ----------------------------
# STATUS CHECK
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "AskPNT AI vNext Running 🚀"

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
