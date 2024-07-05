import re
import os
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from groq import Groq
from threading import Thread
from pathlib import Path
from contextlib import suppress
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

client = Groq(
    api_key="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",
)

genai.configure(api_key="AIzaSyD5y-XacGiB14vcEV-GaqmPAzXDGMulPdA")
generation_config = {"temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}
model = genai.GenerativeModel("gemini-pro-vision", generation_config=generation_config)
model2 = genai.GenerativeModel("gemini-pro", generation_config=generation_config)

system_prompt = [
    {
        "role": "system",
        "content": (
            "You are a friendly and knowledgeable medical assistant named Hackalife Doctor AI. Provide accurate and reliable "
            "medical information, answer health-related questions, and offer general advice. Maintain an informal, friendly tone. "
            "You were made by the Hackalife team. Always structure your responses with the following sections when applicable: "
            "Uses:, How it works:, Dosage and administration:, Side effects:, Precautions and warnings:, and Remember, it's always a good idea to talk to your doctor or pharmacist before taking any new medication. "
            "Remember to always recommend consulting a healthcare professional for serious issues or diagnoses. Use <br> tags for line breaks., also use ** ** for bolding text. Note You Are Being Used IN A WEBSITE"
            "Remember when they ask for medicine or the picture you must tell about the usage"
            "Dont Do Mistakes Like Using ** * Instead of ** **"
            "Use <h3> </h3> For Big Titles"
        )
    }
]
messages = []

def dynamic_format_response(response):
    sections = [
        r'Uses:',
        r'How it works:',
        r'Dosage and administration:',
        r'Side effects:',
        r'Precautions and warnings:',
        r'Remember, it\'s always a good idea to talk to your doctor or pharmacist before taking any new medication'
    ]
    
    for section in sections:
        response = re.sub(f"({section})", r"<br><br>\1<br>", response)

    response = re.sub(r'\* ([^\n]*)', r'<br>• \1', response)
    response = re.sub(r'(• [^\n]*)', r'\1<br>', response)

    return response

def gpt_response(message, context):
    global messages

    if len(messages) > 20:
        messages.pop(0)
        messages.pop(0)

    messages.append({"role": "user", "content": message})
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=system_prompt + context + messages
    )
    formatted_response = dynamic_format_response(response.choices[0].message.content)
    messages.append({"role": "assistant", "content": formatted_response})
    return formatted_response

@app.route("/")
def home():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message")

    if 'chat_history' not in session:
        session['chat_history'] = []

    context = session['chat_history']
    bot_response = gpt_response(user_message, context)

    # Append messages to chat history in session
    session['chat_history'].append({"role": "user", "content": user_message})
    session['chat_history'].append({"role": "assistant", "content": bot_response})

    return jsonify({"response": bot_response})

@app.route("/upload", methods=["POST"])
def upload():
    question = request.form.get("message")
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = file.filename
        file.save(filename)

        try:
            image_part = {
                "mime_type": "image/jpeg",
                "data": Path(filename).read_bytes()
            }

            prompt_parts = [
                f"{question}\n",
                image_part
            ]

            response = model.generate_content(prompt_parts)
            os.remove(filename)
            
            if 'chat_history' not in session:
                session['chat_history'] = []

            # Append messages to chat history in session
            session['chat_history'].append({"role": "user", "content": question})
            session['chat_history'].append({"role": "assistant", "content": response.text})
            
            return jsonify({"response": response.text})
        except Exception as e:
            with suppress(FileNotFoundError):
                os.remove(filename)
            return jsonify({"error": str(e)}), 500

@app.route("/history", methods=["GET"])
def history():
    return jsonify(session.get('chat_history', []))

def run():
    app.run(debug=False)

def dashboard():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    dashboard()
