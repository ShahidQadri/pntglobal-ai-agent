from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# -------------------------
# Knowledge Base (REAL DATA ONLY)
# -------------------------

SERVICES = {
    "seo": {
        "name": "SEO & xSEO",
        "description": "We provide SEO and xSEO services including GEO, AEO, AIO, and SXO to improve visibility across search and AI platforms."
    },
    "gmb": {
        "name": "Google Business Profile Optimization",
        "description": "We optimize and manage Google Business Profiles to improve local visibility and lead generation."
    }
}

FAQS = {
    "what services do you offer": "PNT Global offers SEO, xSEO, Google Business Profile optimization, and digital growth solutions.",
    "how long have you been in business": "PNT Global has over 25 years of experience in IT and digital services."
}

# -------------------------
# Intent Detection
# -------------------------

def detect_intent(text):
    text = text.lower()

    if any(k in text for k in ["price", "pricing", "cost"]):
        return "pricing", 0.8

    if any(k in text for k in ["seo", "xseo", "search"]):
        return "service_inquiry", 0.75

    for faq in FAQS:
        if faq in text:
            return "faq", 0.9

    return "unknown", 0.4

# -------------------------
# Escalation Check
# -------------------------

def should_escalate(confidence):
    return confidence < 0.6

# -------------------------
# Chat Endpoint
# -------------------------

@app.route("/agent-chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "").strip()

    if not msg:
        return jsonify({"reply": "Please type your question so I can help."})

    intent, confidence = detect_intent(msg)

    # FAQ RESPONSE
    if intent == "faq":
        for q, a in FAQS.items():
            if q in msg.lower():
                return jsonify({
                    "reply": a,
                    "confidence": confidence
                })

    # SERVICE RESPONSE
    if intent == "service_inquiry":
        return jsonify({
            "reply": (
                f"{SERVICES['seo']['description']} "
                "Are you asking about a local business or an online brand?"
            ),
            "confidence": confidence
        })

    # PRICING RESPONSE
    if intent == "pricing":
        return jsonify({
            "reply": (
                "Pricing depends on scope and goals. "
                "Is your business local, eCommerce, or enterprise-level?"
            ),
            "confidence": confidence
        })

    # ESCALATION
    if should_escalate(confidence):
        return jsonify({
            "reply": (
                "I want to make sure you get the right guidance. "
                "May I connect you with a PNT specialist?"
            ),
            "escalate": True,
            "confidence": confidence
        })

    # FALLBACK
    return jsonify({
        "reply": "Could you clarify what you’d like help with?",
        "confidence": confidence
    })

# -------------------------
# App Runner
# -------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
