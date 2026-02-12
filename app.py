from flask import Flask, request, jsonify
import re

app = Flask(__name__)

def detect_intent(text):
    text = text.lower()
    if "seo" in text:
        return "seo"
    if "price" in text or "pricing" in text:
        return "pricing"
    return "general"

@app.route("/agent-chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message","")

    intent = detect_intent(msg)

    if intent == "seo":
        reply = "PNT Global offers SEO and xSEO services with 25+ years experience."
    elif intent == "pricing":
        reply = "Pricing depends on scope. Is your business local, eCommerce, or enterprise?"
    else:
        reply = "Thank you for contacting PNT Global. Please tell me more."

    return jsonify({"reply": reply})

@app.after_request
def cors(res):
    res.headers["Access-Control-Allow-Origin"] = "https://pntglobal.com"
    res.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return res

if __name__ == "__main__":
    app.run()
