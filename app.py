from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import json
from config.firebase_config import get_firebase_config

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Initialize Firebase (with error handling for serverless environment)
firebase_app = None
try:
    if not firebase_admin._apps:  # Only initialize if not already initialized
        if os.getenv('FIREBASE_CREDENTIALS'):
            cred_dict = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback to file (development only)
            cred = credentials.Certificate("firebase-key.json")
        
        firebase_app = firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Firebase initialization error: {e}")

@app.route('/')
def index():
    # Pass Firebase config to template
    return render_template('index.html', firebase_config=get_firebase_config())

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        if not firebase_app:
            return jsonify({"error": "Firebase not initialized"}), 500
        
        docs = db.collection('collection_name').stream()
        items = [doc.to_dict() for doc in docs]
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Vercel requires this for serverless deployment
app.debug = os.getenv('DEBUG', 'False').lower() == 'true'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 