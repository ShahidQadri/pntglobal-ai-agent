from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid

app = Flask(__name__)
CORS(app)

# ----------------------------
# IN-MEMORY SESSION STORE
# ----------------------------
sessions = {}

def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            "clarified": False,
            "lead_stage": None,
            "lead": {}
        }
    return sessions[session_id]

# ----------------------------
# SERVICES & PRICING
# ----------------------------
services = {
    "seo": "Search Engine Optimization — US$ 200 per month",
    "social media": "Social Media Management — US$ 150 per month",
    "digital marketing": "Digital Marketing — US$ 250 per month",
    "google business": "Google Business Optimization — US$ 100",
    "wordpress": "WordPress website design — US$ 350 (One time)",
    "html": "HTML (CSS, JS) website design — US$ 250 (One time)",
    "woocommerce": "WooCommerce online store — US$ 450 (One time)",
    "shopify": "Shopify online store — US$ 450 (One time)",
    "laravel store": "PHP (Laravel) online store — US$ 650 (One time)",
    "software": "PHP (Laravel) software development — US$ 15 per hour",
}

# ----------------------------
# FAQs
# ----------------------------
faq = {
    "location": {
        "keywords": ["where", "based", "location", "office", "address"],
        "answer": "Our head office is located at A-7, 4th Floor, Namco Campbell Street, Karachi – 74200, Pakistan. We serve clients worldwide."
    },
    "contact": {
        "keywords": ["contact", "email", "phone", "call", "reach"],
        "answer": "You can contact us at +92-335-363-6051 or email Consultant@PNTGlobal.com."
    },
    "consultation": {
        "keywords": ["free", "consultation", "audit"],
        "answer": "Yes, we offer free consultations and SEO audits before starting any project."
    }
}

# ----------------------------
# AGENT CORE
# ----------------------------
def agent_reply(text, session):
    text_lower = text.lower()

    # ----------------------------
    # GREETINGS (NEW)
    # ----------------------------
    greetings = ["hi", "hello", "hey", "how are you", "assalam", "salam"]
    if any(g in text_lower for g in greetings):
        return {
            "reply": "Hello 👋 How can I help you today?",
            "intent": "greeting",
            "confidence": 1.0
        }

    # ----------------------------
    # PRICE INTENT (STRICT)
    # ----------------------------
    price_words = ["price", "pricing", "cost", "charges", "rate", "fee"]

    if any(pw in text_lower for pw in price_words):
        for key, price_text in pricing.items():
            if key in text_lower:
                return {
                    "reply": price_text,
                    "intent": "pricing",
                    "confidence": 0.9
                }

        return {
            "reply": "Sure — which service would you like pricing for?",
            "intent": "pricing_clarification",
            "confidence": 0.7
        }

    # ----------------------------
    # LEAD CAPTURE FLOW
    # ----------------------------
    if session["lead_stage"] == "name":
        session["lead"]["name"] = text.title()
        session["lead_stage"] = "contact"
        return {
            "reply": "Thanks! Please share your email or WhatsApp number.",
            "intent": "lead_capture"
        }

    if session["lead_stage"] == "contact":
        session["lead"]["contact"] = text
        session["lead_stage"] = "complete"
        return {
            "reply": "Perfect 👍 A PNT specialist will contact you shortly.",
            "intent": "lead_complete",
            "lead": session["lead"]
        }

    # ----------------------------
    # SERVICE DETAILS (NO PRICE)
    # ----------------------------
    for key, description in services.items():
        if key in text_lower:
            return {
                "reply": (
                    f"{description} "
                    "Would you like to know the **process**, **use cases**, or **pricing**?"
                ),
                "intent": "service_detail",
                "confidence": 0.85
            }

    # ----------------------------
    # FAQs
    # ----------------------------
    for item in faq.values():
        for kw in item["keywords"]:
            if kw in text_lower:
                return {
                    "reply": item["answer"],
                    "intent": "faq",
                    "confidence": 0.9
                }

    # ----------------------------
    # CONFUSION → ESCALATE
    # ----------------------------
    confusion = ["not sure", "confused", "dont understand", "help me"]
    if any(c in text_lower for c in confusion):
        session["lead_stage"] = "name"
        return {
            "reply": (
                "I want to make sure you get the right guidance. "
                "May I have your name so I can connect you with a specialist?"
            ),
            "intent": "escalation",
            "confidence": 0.3,
            "escalate": True
        }

    # ----------------------------
    # SMART FOLLOW-UP (ONLY ONCE)
    # ----------------------------
    if not session["clarified"]:
        session["clarified"] = True
        return {
            "reply": (
                "Could you tell me what you’re looking for — "
                "**website**, **online store**, or **marketing**?"
            ),
            "intent": "clarification",
            "confidence": 0.6
        }

    # ----------------------------
    # FINAL ESCALATION
    # ----------------------------
    session["lead_stage"] = "name"
    return {
        "reply": (
            "To make sure you get the right help, "
            "let me connect you with a PNT expert. May I have your name?"
        ),
        "intent": "escalation",
        "confidence": 0.4,
        "escalate": True
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
    response = agent_reply(msg, session)
    response["session_id"] = session_id

    return jsonify(response)

# ----------------------------
# STATUS CHECK
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "AskPNT Agentic AI v3 is running ✅"

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
