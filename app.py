from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Allow all origins

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
# FAQ KEYWORDS → ANSWERS
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
# INTENT DETECTION
# ----------------------------
def get_reply(text):
    text = text.lower()

    # 1️⃣ Check services & pricing first
    for key, reply in services.items():
        if key in text:
            return reply

    # 2️⃣ Check FAQs (keyword-based)
    for item in faq.values():
        for kw in item["keywords"]:
            if kw in text:
                return item["answer"]

    # 3️⃣ Default response
    return "Thank you for contacting PNT Global. Please tell me more about your requirement."

# ----------------------------
# CHAT ENDPOINT
# ----------------------------
@app.route("/agent-chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "")
    reply = get_reply(msg)
    return jsonify({"reply": reply})

# ----------------------------
# ROOT (STATUS CHECK)
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "PNT Global AI Agent is running ✅"

# ----------------------------
# RUN APP (RENDER)
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
