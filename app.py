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
{PNT_KNOWLEDGE}

CONVERSATION MEMORY:
{json.dumps(session_context, ensure_ascii=False, indent=2)}

CURRENT USER MESSAGE:
{user_message}

IMPORTANT RULES:

1. Use the company knowledge to answer questions about PNT Global.
2. Use the conversation memory so the visitor does not have to repeat
   information already provided.
3. Continue the conversation naturally from the previous messages.
4. Never invent PNT Global services, prices, features, clients,
   guarantees or other company information.
5. If the knowledge base does not contain the answer, say that the
   PNT Global team can provide the specific information.
6. Keep responses short, clear and conversational.
7. Do not sound like a generic AI chatbot.
8. Do not aggressively sell.
9. Ask only ONE question at a time when a question is genuinely needed.
    Do not ask a question merely to avoid making a recommendation.
10. If the visitor is discussing a particular service, remember that
    service and keep the conversation relevant to it.
11. If the visitor clearly wants to be contacted or requests a quotation,
    set lead_capture to true.
12. Do not collect or invent lead information. The Flask application
    handles lead capture.
13. Return ONLY valid JSON. No markdown and no explanation outside JSON.

CONVERSATION MEMORY RULES:

14. Review the conversation history before answering.
15. Treat information already provided by the visitor as known information.
16. Do not ask the visitor to repeat information already available.
17. Resolve words such as "it", "this", "that", "me", "my business",
    "my website" and "what would you recommend?" using the conversation.
18. If the visitor has already identified a business type or service,
    use that information in your response.
19. Identify the main PNT Global service being discussed in the current
    conversation.
20. If a service has already been identified in the conversation,
    keep that service as the current service unless the visitor clearly
    changes the subject.
21. If no specific PNT Global service has been identified yet, return null
    for service.
22. When the visitor asks "what would you recommend?", "what should I do?",
    "what is best for me?" or similar recommendation questions, do not ask
    them to repeat information already available in conversation memory.
23. If a current service is already identified, make a practical recommendation
    related to that service using the company knowledge.
24. If the visitor has an online store and Shopify is the current service,
    recommend Shopify development and/or growth management as appropriate,
    rather than asking what area they want to improve.
25. Only ask a follow-up question if the available conversation context is
    genuinely insufficient to make a useful recommendation.

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
