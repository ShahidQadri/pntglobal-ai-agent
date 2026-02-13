from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Allow all origins

# ----------------------------
# SERVICES & PRICING
# ----------------------------
services_info = {
    "websites": {
        "html": "HTML (CSS, JS) website design — US$ 250 (One time)",
        "wordpress": "WordPress website design — US$ 350 (One time)"
    },
    "online_store": {
        "woocommerce": "WooCommerce store — US$ 450 (One time)",
        "shopify": "Shopify store — US$ 450 (One time)",
        "php_laravel": "PHP (Laravel) store — US$ 650 (One time)"
    },
    "software_development": {
        "php_laravel": "PHP (Laravel) software development — US$ 15 per hour"
    },
    "seo": "Search Engine Optimization — US$ 200 per month",
    "social_media": "Social Media Management — US$ 150 per month",
    "digital_marketing": "Digital Marketing — US$ 250 per month",
    "google_business": "Google Business Optimization — US$ 100"
}

# ----------------------------
# FAQ
# ----------------------------
faq_info = {
    "where is pnt global based": "Our head office is at A-7, 4th Floor, Namco Campbell Street, Karachi – 74200, Pakistan. We serve clients worldwide.",
    "what makes pnt global different": "With over 25 years of experience, we have a skilled in-house team, long-term client relationships, affordable yet premium service packages, and end-to-end digital solutions under one roof.",
    "do you provide free consultations": "Yes, we offer free consultations and SEO audits to help businesses identify opportunities before starting a project.",
    "can your solutions scale": "Absolutely. From startups to enterprises, our solutions are flexible, scalable, and customized to grow with your business needs.",
    "can pnt global manage my digital presence": "Yes. From website development and SEO to social media, hosting, and branding, we provide a complete 360° digital management solution.",
    "what industries do you serve": "We work with businesses of all sizes across industries including e-commerce, retail, hospitality, healthcare, technology, and startups.",
    "how do i get in touch": "Phone: +92-335-363-6051 | Email: Consultant@PNTGlobal.com | Address: A-7, 4th Floor, Namco Campbell Street, Karachi – 74200, Pakistan",
    "are your services affordable": "Yes. We design cost-effective packages without compromising quality, ideal for both small and large businesses.",
    "do you provide services internationally": "Yes. PNT Global works with clients in the US, UAE, UK, and more, delivering solutions tailored to diverse business environments."
}

# ----------------------------
# Intent detection
# ----------------------------
def detect_intent(text):
    text = text.lower()

    # Check FAQs first (keyword match)
    for q in faq_info:
        if q in text:
            return faq_info[q]

    # Check services / pricing
    for key, info in services_info.items():
        if key in text:
            if isinstance(info, dict):
                for subcat, desc in info.items():
                    if subcat in text:
                        return desc
            else:
                return info

    # Default reply
    return "Thank you for contacting PNT Global. Please tell me more."

# ----------------------------
# API Endpoint
# ----------------------------
@app.route("/agent-chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "")
    reply = detect_intent(msg)
    return jsonify({"reply": reply})

# ----------------------------
# Optional: root route for testing
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "PNT Global AI Agent is running ✅"

# ----------------------------
# Run Flask
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
