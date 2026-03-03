from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. Initialize Flask App ---
app = Flask(__name__)
# CORS allows your GitHub Pages website to talk to this Python server
CORS(app) 

# --- 2. Initialize Firebase ---
# Make sure serviceAccountKey.json is in the same folder
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Connected")
except Exception as e:
    print(f"Firebase Error: {e}")

# --- 3. The API Endpoint ---
@app.route('/chat', methods=['POST'])
def chat():
    # Get the message from the website
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
        
        # Handle benefits (list or string)
        raw_benefits = herb_data.get('benefits', [])
        if isinstance(raw_benefits, list):
            benefits_str = " ".join(raw_benefits).lower()
        else:
            benefits_str = str(raw_benefits).lower()

        # Check for match
        if user_message in name or user_message in category or user_message in benefits_str:
            found_herbs.append(herb_data)

    # Format the reply
    if not found_herbs:
        reply = f"I couldn't find information about '{user_message}'. Try 'Brahmi' or 'Immunity'."
    else:
        reply_lines = []
        for herb in found_herbs:
            # Create a clean text response
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

# --- 4. Run the Server ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)