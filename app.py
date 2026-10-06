from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
import requests

from knowledge_base import PNT_KNOWLEDGE
from agent_rules import ASKPNT_RULES


# ============================================================
# OpenRouter Configuration
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def call_ai(prompt):
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://pntglobal.com",
                "X-Title": "AskPNT"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("OPENROUTER ERROR:", e)
        return None


# ============================================================
# Flask Application
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# Session Memory
# ============================================================

sessions = {}


def get_session(session_id):

    if session_id not in sessions:

        sessions[session_id] = {

            # Lead / conversation stage
            "lead_stage": None,

            # Business memory
            "business_type": None,
            "service": None,
            "business_goal": None,
            "requirement": None,
            "challenge": None,
            "target_market": None,
            "platform": None,
            "budget": None,
            "timeline": None,

            # Conversation
            "history": [],
            "last_question": None,

            # Lead information
            "lead": {},

            # Session creation time
            "created_at": str(datetime.now())
        }

    return sessions[session_id]


# ============================================================
# JSON Response Parser
# ============================================================

def extract_json(text):

    try:

        start = text.find("{")
        end = text.rfind("}") + 1

        if start != -1 and end != -1:

            return json.loads(
                text[start:end]
            )

    except Exception as e:

        print("JSON PARSE ERROR:", e)

    return {

        "reply": text,

        "intent": "unknown",

        "lead_capture": False,

        "next_question": None,

        "service": None,

        "business_type": None,

        "business_goal": None,

        "requirement": None,

        "challenge": None,

        "target_market": None,

        "platform": None,

        "budget": None,

        "timeline": None
    }


# ============================================================
# AskPNT AI Agent
# ============================================================

def ai_agent_reply(user_message, session):

    # --------------------------------------------------------
    # Conversation Memory sent to AI
    # --------------------------------------------------------

    session_context = {

        "lead_stage": session.get("lead_stage"),

        "business_type": session.get("business_type"),

        "service": session.get("service"),

        "business_goal": session.get("business_goal"),

        "requirement": session.get("requirement"),

        "challenge": session.get("challenge"),

        "target_market": session.get("target_market"),

        "platform": session.get("platform"),

        "budget": session.get("budget"),

        "timeline": session.get("timeline"),

        "last_question": session.get("last_question"),

        "lead": session.get("lead", {}),

        # Send recent conversation only
        "history": session.get("history")[-5:]
    }


    print("SESSION CONTEXT:", session_context)


    # --------------------------------------------------------
    # AI Prompt
    # --------------------------------------------------------

    prompt = f"""
You are AskPNT, the AI sales assistant for PNT Global.

Your role is to have a natural, helpful conversation with website
visitors and help them understand PNT Global's services.

You should behave like a knowledgeable business assistant,
not like an aggressive salesperson.

============================================================
COMPANY KNOWLEDGE
============================================================

{PNT_KNOWLEDGE}


============================================================
ASKPNT RULES
============================================================

{ASKPNT_RULES}


============================================================
CONVERSATION MEMORY
============================================================

{json.dumps(session_context, ensure_ascii=False, indent=2)}


============================================================
CURRENT USER MESSAGE
============================================================

{user_message}


============================================================
IMPORTANT MEMORY RULES
============================================================

Use the conversation memory when answering the current message.

Do NOT ask the visitor to repeat information that is already available
in the conversation memory.

If the visitor asks for a recommendation, use the information already
known about their business, goal, requirement, challenge, platform,
service or target market.

Only ask a new question when genuinely necessary.

If the visitor provides new information, update the appropriate memory
field.

If the visitor clearly corrects previous information, use the new
information instead.

Never invent missing information.

If information is not available, use null.

============================================================
MEMORY FIELDS
============================================================

The following fields should contain information identified from the
conversation.

business_type:
The type of business, such as:
"Online Store"
"Textile Manufacturer"
"Restaurant"
"IT Company"
"Export Business"

service:
The PNT Global service currently being discussed, such as:
"Shopify"
"SEO"
"WordPress"
"Website Development"
"Software Development"
"AI Solutions"
"eCommerce Solutions"

business_goal:
The main objective, such as:
"Increase Sales"
"Generate Leads"
"Improve SEO Visibility"
"Improve AI Search Visibility"
"Build an Ecommerce Store"
"Automate Business Processes"

requirement:
The specific thing the visitor needs.

challenge:
The problem or difficulty the visitor is trying to solve.

target_market:
The market, country, region or audience the visitor wants to target.

platform:
The technology or platform currently being used, such as:
"Shopify"
"WooCommerce"
"WordPress"
"Laravel"
"Custom"

budget:
The budget mentioned by the visitor.

timeline:
The expected timeframe mentioned by the visitor.

If any information is not available, return null.

Do not invent missing information.


============================================================
INTENT OPTIONS
============================================================

Use one of:

- greeting
- service_detail
- pricing
- faq
- lead_capture
- unknown


============================================================
RESPONSE FORMAT
============================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
  "reply": "short natural response",
  "intent": "greeting|service_detail|pricing|faq|lead_capture|unknown",
  "lead_capture": false,
  "next_question": null,
  "service": null,
  "business_type": null,
  "business_goal": null,
  "requirement": null,
  "challenge": null,
  "target_market": null,
  "platform": null,
  "budget": null,
  "timeline": null
}}


============================================================
REPLY GUIDELINES
============================================================

Keep the response natural and reasonably short.

Do not repeat the entire company knowledge.

Do not make unsupported claims.

Do not invent prices.

Do not invent clients.

Do not invent guarantees.

Do not invent services.

Do not aggressively sell.

Use the visitor's existing context whenever possible.

Ask only one question at a time when a question is genuinely needed.

If no question is needed:

"next_question" should be null.

The "reply" should still be useful even when no question is asked.
"""


    # --------------------------------------------------------
    # Call AI
    # --------------------------------------------------------

    text = call_ai(prompt)


    # --------------------------------------------------------
    # AI unavailable
    # --------------------------------------------------------

    if not text:

        return {

            "reply": "AI service temporarily unavailable. Please try again.",

            "intent": "unknown",

            "lead_capture": False,

            "next_question": None,

            "service": None,

            "business_type": None,

            "business_goal": None,

            "requirement": None,

            "challenge": None,

            "target_market": None,

            "platform": None,

            "budget": None,

            "timeline": None
        }


    print("AI RAW:", text)


    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    return extract_json(text)


# ============================================================
# Chat API
# ============================================================

@app.route("/agent-chat", methods=["POST"])
def chat():

    data = request.get_json() or {}

    msg = data.get("message", "").strip()

    # Use existing session ID or create a new one
    session_id = data.get("session_id") or str(uuid.uuid4())


    # --------------------------------------------------------
    # Empty message
    # --------------------------------------------------------

    if not msg:

        return jsonify({
            "reply": "Please send a message.",
            "session_id": session_id
        })


    # --------------------------------------------------------
    # Get session
    # --------------------------------------------------------

    session = get_session(session_id)


    # --------------------------------------------------------
    # Generate AI response
    # --------------------------------------------------------

    response = ai_agent_reply(
        msg,
        session
    )


    # ========================================================
    # Update Conversation Memory
    # ========================================================

    # Last question
    session["last_question"] = response.get(
        "next_question"
    )


    # Lead stage
    if response.get("lead_capture"):

        session["lead_stage"] = "capture"


    # --------------------------------------------------------
    # Business Memory Fields
    # --------------------------------------------------------

    memory_fields = [

        "business_type",

        "service",

        "business_goal",

        "requirement",

        "challenge",

        "target_market",

        "platform",

        "budget",

        "timeline"
    ]


    for field in memory_fields:

        value = response.get(field)

        if value:

            session[field] = value


    # ========================================================
    # Conversation History
    # ========================================================

    session["history"].append({

        "user": msg,

        "bot": response.get(
            "reply",
            ""
        ),

        "time": str(
            datetime.now()
        )
    })


    # Keep last 10 exchanges
    session["history"] = session["history"][-10:]


    # ========================================================
    # Return Session ID
    # ========================================================

    response["session_id"] = session_id


    # ========================================================
    # Debug
    # ========================================================

    print("UPDATED SESSION:", session)


    return jsonify(response)


# ============================================================
# Health / Home Route
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return "AskPNT AI vNext Running 🚀"


# ============================================================
# Run Application
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
