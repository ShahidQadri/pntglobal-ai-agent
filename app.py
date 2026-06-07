from flask import Flask, request, jsonify
from flask_cors import CORS
import os, uuid
from datetime import datetime
import google.generativeai as genai
import json
import google.generativeai as genai
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
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
# AI agent reply
# ----------------------------
# ----------------------------
# AI agent reply
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

User: {user_message}
Context: {json.dumps(session_context)}

Return ONLY valid JSON:
{{
  "reply": "short response",
  "intent": "greeting|service_detail|pricing|faq|lead_capture|unknown",
  "lead_capture": false,
  "next_question": null
}}
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        print("GEMINI RAW RESPONSE:", response.text)  # 👈 ADD THIS
        text = response.text.strip()

        import json, re

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())

        # fallback (VERY important)
        return {
            "reply": text,
            "intent": "unknown",
            "lead_capture": False,
            "next_question": None
        }

    except Exception as e:
        print("GEMINI ERROR:", e)

        return {
            "reply": "Sorry, I couldn't process that right now.",
            "intent": "unknown",
            "lead_capture": False,
            "next_question": None
        }
        
# ----------------------------
# Chat endpoint
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

    # Lead capture flow
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

    # Add to session history
    session["history"].append({
        "user": msg,
        "bot": response["reply"],
        "time": str(datetime.now())
    })
    response["session_id"] = session_id

    return jsonify(response)

# ----------------------------
# Status check
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "AskPNT AI vNext Running 🚀"

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
