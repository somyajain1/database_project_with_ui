from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import json
from config.firebase_config import get_firebase_config
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Initialize Firebase (with error handling for serverless environment)
firebase_app = None

def init_firebase():
    global firebase_app
    if not firebase_admin._apps:
        try:
            if os.getenv('FIREBASE_CREDENTIALS'):
                cred_dict = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
                cred = credentials.Certificate(cred_dict)
            else:
                # Fallback to file (development only)
                cred = credentials.Certificate("firebase-key.json")
            
            firebase_app = firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            return None
    return firestore.client()

@app.route('/')
def index():
    return render_template('index.html', firebase_config=get_firebase_config())

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    try:
        db = init_firebase()
        if not db:
            return jsonify({"error": "Firebase not initialized"}), 500

        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({"error": "Email is required"}), 400

        # Store in 'subscribers' collection
        doc_ref = db.collection('subscribers').document()
        doc_ref.set({
            'email': email,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'active'
        })

        return jsonify({"message": "Successfully subscribed"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        db = init_firebase()
        if not db:
            return jsonify({"error": "Firebase not initialized"}), 500
        
        docs = db.collection('collection_name').stream()
        items = [doc.to_dict() for doc in docs]
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for Vercel
app.debug = os.getenv('DEBUG', 'False').lower() == 'true'

# This is important for Vercel
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 