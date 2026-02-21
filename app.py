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
    text = text.lower()

    # LEAD CAPTURE FLOW
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
            "reply": (
                "Perfect 👍 A PNT specialist will contact you shortly. "
                "Thank you for reaching out!"
            ),
            "intent": "lead_complete",
            "lead": session["lead"]
        }

    # SERVICES
    for key, reply in services.items():
        if key in text:
            return {
                "reply": reply,
                "intent": "service_pricing",
                "confidence": 0.8
            }

    # FAQs
    for item in faq.values():
        for kw in item["keywords"]:
            if kw in text:
                return {
                    "reply": item["answer"],
                    "intent": "faq",
                    "confidence": 0.9
                }

    # CONFUSION → ESCALATE
    confusion = ["not sure", "confused", "dont understand", "help me"]
    if any(c in text for c in confusion):
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

    # SMART FOLLOW-UP (ONLY ONCE)
    if not session["clarified"]:
        session["clarified"] = True
        return {
            "reply": (
                "Got it. Are you looking for **website development**, "
                "**online store**, or **digital marketing** services?"
            ),
            "intent": "clarification",
            "confidence": 0.6
        }

    # FINAL FALLBACK → ESCALATE
    session["lead_stage"] = "name"
    return {
        "reply": (
            "To avoid any confusion, let me connect you with a PNT expert. "
            "May I have your name?"
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
