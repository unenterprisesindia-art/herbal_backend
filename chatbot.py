from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64

app = Flask(__name__)

# --- MANUAL CORS FIX ---
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    # FIXED LINE BELOW (Added the = sign)
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response
# -----------------------

# Initialize Firebase
try:
    firebase_key_b64 = os.environ.get('FIREBASE_KEY')
    
    if firebase_key_b64:
        # Decode the Base64 string back to JSON
        firebase_key_json = base64.b64decode(firebase_key_b64).decode('utf-8')
        cred_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(cred_dict)
        print("✅ Firebase Connected via Base64 ENV")
    else:
        # Local fallback
        cred = credentials.Certificate("serviceAccountKey.json")
        print("✅ Firebase Connected via File")

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()

except Exception as e:
    print(f"❌ Firebase Init Error: {e}")

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
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