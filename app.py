from flask import Flask, request, jsonify
from flask_cors import CORS
import os, uuid, json
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
            "stage": "discovery",        # discovery, service_followup, lead, lead_complete
            "intent": None,
            "service": None,
            "lead_score": 0,
            "lead": {},
            "history": [],
            "last_question": None,
            "clarified": False,
            "created_at": str(datetime.now())
        }
    return sessions[session_id]

# ----------------------------
# SERVICES & PRICING
# ----------------------------
services = {
    "seo": "Search Engine Optimization to improve rankings and traffic.",
    "social media": "Social Media Management for brand growth.",
    "digital marketing": "Complete digital growth strategy.",
    "wordpress": "WordPress website development.",
    "shopify": "Shopify store setup and customization.",
    "woocommerce": "WooCommerce eCommerce solutions.",
    "laravel": "Custom Laravel software and systems."
}

pricing = {
    "seo": "SEO pricing starts from $300/month depending on scope.",
    "website": "Website development starts from $500.",
    "shopify": "Shopify stores start from $400.",
    "marketing": "Digital marketing packages start from $250/month."
}

faq = {
    "location": {"keywords": ["where", "location", "office"], "answer": "We are based in Karachi, Pakistan and serve globally."},
    "contact": {"keywords": ["contact", "phone", "email"], "answer": "Call +92-335-363-6051 or email Consultant@PNTGlobal.com"}
}

# ----------------------------
# INTENT DETECTION (Basic placeholder; replace with AI for full version)
# ----------------------------
def detect_intent(text):
    text = text.lower()
    if any(x in text for x in ["price", "cost", "charges"]):
        return "pricing"
    if any(x in text for x in ["seo", "marketing", "website", "shopify", "woocommerce", "laravel"]):
        return "service"
    if any(x in text for x in ["hi", "hello", "salam"]):
        return "greeting"
    if any(x in text for x in ["help", "confused"]):
        return "confused"
    return "unknown"

def detect_service(text):
    text = text.lower()
    for key in services.keys():
        if key in text:
            return key
    return None

def update_lead_score(session, text):
    text = text.lower()
    if "business" in text: session["lead_score"] += 5
    if "budget" in text or "$" in text: session["lead_score"] += 10
    if "urgent" in text: session["lead_score"] += 10

# ----------------------------
# AGENT CORE
# ----------------------------
def agent_reply(text, session):
    text_lower = text.lower().strip()
    session["history"].append({"user": text, "time": str(datetime.now())})

    # ----------------------------
    # Handle YES/NO Responses
    # ----------------------------
    yes_words = ["yes", "yeah", "yep", "ok", "sure"]
    no_words = ["no", "nah", "not really", "nope"]

    if session.get("last_question"):
        if text_lower in yes_words:
            if session["last_question"] == "service_followup":
                session["last_question"] = "followup"
                return {"reply": "Great 👍 Do you want **pricing**, **process**, or **case studies**?", "intent": "followup"}
            if session["last_question"] == "clarification":
                session["last_question"] = None
                return {"reply": "Are you looking for **website**, **marketing**, or an **online store**?", "intent": "clarification"}
        if text_lower in no_words:
            session["last_question"] = None
            return {"reply": "No worries 🙂 Can you tell me what service you are interested in?", "intent": "clarification"}

    # ----------------------------
    # Detect intent/service
    # ----------------------------
    intent = detect_intent(text)
    service = detect_service(text)
    session["intent"] = intent
    if service: session["service"] = service
    update_lead_score(session, text)

    # ----------------------------
    # GREETING
    # ----------------------------
    if intent == "greeting":
        return {"reply": "Hello 👋 How can I assist your business today?", "intent": intent}

    # ----------------------------
    # PRICING
    # ----------------------------
    if intent == "pricing":
        if session.get("service") and session["service"] in pricing:
            return {"reply": pricing[session["service"]], "intent": intent}
        session["last_question"] = "pricing_clarification"
        return {"reply": "Sure — which service are you interested in?", "intent": "pricing_clarification"}

    # ----------------------------
    # SERVICE DETAILS
    # ----------------------------
    if intent == "service" and session.get("service"):
        session["last_question"] = "service_followup"
        return {"reply": f"{services[session['service']]} Would you like to know the **process**, **use cases**, or **pricing**?", "intent": "service_detail"}

    # ----------------------------
    # FAQ
    # ----------------------------
    for item in faq.values():
        for kw in item["keywords"]:
            if kw in text_lower:
                return {"reply": item["answer"], "intent": "faq"}

    # ----------------------------
    # LEAD CAPTURE (smart)
    # ----------------------------
    if session["lead_score"] >= 10 and session["stage"] == "discovery":
        session["stage"] = "lead"
        session["last_question"] = "lead_name"
        return {"reply": "I can connect you with a specialist. May I have your name?", "intent": "lead_start"}

    if session["stage"] == "lead" and "name" not in session["lead"]:
        session["lead"]["name"] = text
        session["last_question"] = "lead_contact"
        return {"reply": "Great! Please share your email or WhatsApp number.", "intent": "lead_contact"}

    if session["stage"] == "lead" and "contact" not in session["lead"]:
        session["lead"]["contact"] = text
        session["stage"] = "lead_complete"
        session["last_question"] = None
        return {"reply": "Perfect 👍 Our team will contact you shortly.", "intent": "lead_complete", "lead": session["lead"]}

    # ----------------------------
    # CONFUSED
    # ----------------------------
    if intent == "confused":
        session["last_question"] = "clarification"
        return {"reply": "No worries 🙂 Are you looking for a **website**, **marketing**, or an **online store**?", "intent": "confused"}

    # ----------------------------
    # DEFAULT SMART PROMPT
    # ----------------------------
    if not session["clarified"]:
        session["clarified"] = True
        session["last_question"] = "clarification"
        return {"reply": "Could you tell me what you’re looking for — **website**, **online store**, or **marketing**?", "intent": "clarification", "confidence": 0.6}

    return {"reply": "Can you tell me if you need help with **website development**, **SEO**, or **marketing**?", "intent": "clarification"}

# ----------------------------
# ROUTES
# ----------------------------
@app.route("/agent-chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    session = get_session(session_id)
    response = agent_reply(msg, session)
    response["session_id"] = session_id
    response["lead_score"] = session["lead_score"]
    return jsonify(response)

@app.route("/", methods=["GET"])
def home():
    return "AskPNT Agentic AI vNext Running 🚀"

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
