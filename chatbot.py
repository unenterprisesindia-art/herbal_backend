from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# --- MANUAL CORS FIX (Works perfectly on Vercel) ---
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response
# --------------------------------------------------

# Initialize Firebase
# We check if the app is already initialized to avoid errors on reload
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase Init Error: {e}")

db = firestore.client()

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    # Handle Preflight Request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json()
    user_message = data.get('message', '').lower().strip()

    if not user_message:
        return jsonify({'reply': "Please type something."})

    # Search Logic
    herbs_ref = db.collection("herbs")
    docs = herbs_ref.stream()
    
    found_herbs = []
    
    for doc in docs:
        herb_data = doc.to_dict()
        name = herb_data.get('name', '').lower()
        category = herb_data.get('category', '').lower()
        
        raw_benefits = herb_data.get('benefits', [])
        if isinstance(raw_benefits, list):
            benefits_str = " ".join(raw_benefits).lower()
        else:
            benefits_str = str(raw_benefits).lower()

        if user_message in name or user_message in category or user_message in benefits_str:
            found_herbs.append(herb_data)

    if not found_herbs:
        reply = f"I couldn't find information about '{user_message}'. Try 'Brahmi' or 'Immunity'."
    else:
        reply_lines = []
        for herb in found_herbs:
            line = (
                f"🌱 **{herb.get('name')}**\n"
                f"📂 Category: {herb.get('category')}\n"
                f"✨ Benefits: {herb.get('benefits')}\n"
                f"💊 Dosage: {herb.get('dosage')}\n"
                f"⚠️ Precautions: {herb.get('precautions')}"
            )
            reply_lines.append(line)
        reply = "\n\n".join(reply_lines)

    return jsonify({'reply': reply})

# NOTE: We removed app.run() because Vercel handles the server automatically