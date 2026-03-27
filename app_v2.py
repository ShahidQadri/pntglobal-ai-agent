from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# ----------------------------
# SERVICES & PRICING (SOURCE OF TRUTH)
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
    },
    "services": {
        "keywords": ["service", "website", "web", "store", "development"],
        "answer": (
            "We offer Website Design, Online Store Development, "
            "Software Development, SEO, Social Media Management, "
            "Digital Marketing, and Google Business Optimization."
        )
    },
    "difference": {
        "keywords": ["different", "why you", "experience"],
        "answer": (
            "With over 25 years of experience, we provide in-house expertise, "
            "long-term client relationships, and complete digital solutions under one roof."
        )
    }
}

# ----------------------------
# AGENT CORE
# ----------------------------
def agent_reply(text):
    text = text.lower()

    # 1️⃣ Service & Pricing Detection
    for key, reply in services.items():
        if key in text:
            return {
                "reply": reply,
                "intent": "service_pricing",
                "confidence": 0.8
            }

    # 2️⃣ FAQ Detection
    for item in faq.values():
        for kw in item["keywords"]:
            if kw in text:
                return {
                    "reply": item["answer"],
                    "intent": "faq",
                    "confidence": 0.9
                }

    # 3️⃣ Confusion / Unknown
    confusion_words = ["not sure", "confused", "don’t understand", "dont understand", "help me"]
    if any(cw in text for cw in confusion_words):
        return {
            "reply": (
                "I want to make sure you get the right guidance. "
                "May I connect you with a PNT specialist?"
            ),
            "intent": "escalation",
            "confidence": 0.3,
            "escalate": True
        }

    # 4️⃣ General Clarification (Smart Follow-up)
    return {
        "reply": (
            "Sure — are you looking for **website development**, "
            "**online store**, or **digital marketing services**?"
        ),
        "intent": "clarification",
        "confidence": 0.6
    }

# ----------------------------
# CHAT ENDPOINT
# ----------------------------
@app.route("/agent-chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "").strip()

    if not msg:
        return jsonify({"reply": "Please type your question so I can help."})

    response = agent_reply(msg)

    # Auto escalation rule
    if response.get("confidence", 1) < 0.6:
        response["escalate"] = True

    return jsonify(response)

# ----------------------------
# STATUS CHECK
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "PNT Global Agentic AI is running ✅"

# ----------------------------
# RUN APP
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
