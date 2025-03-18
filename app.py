from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv
import os
import json
from config.firebase_config import get_firebase_config
from datetime import datetime

# Load environment variables
load_dotenv()

# Version: 1.0.1 - Adding version tracking for deployment
# Initialize Flask app with debug mode for better error tracking
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, uid, email):
        self.id = uid
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    try:
        user = auth.get_user(user_id)
        return User(user.uid, user.email)
    except:
        return None

# Initialize Firebase Admin SDK
def init_firebase():
    global firebase_app
    if not firebase_admin._apps:
        try:
            print("Attempting to initialize Firebase Admin SDK...")
            # For local development, use service account file
            if os.path.exists('firebase-key.json'):
                print("Using local firebase-key.json file")
                cred = credentials.Certificate('firebase-key.json')
            # For production (Vercel), use environment variable
            elif os.getenv('FIREBASE_CREDENTIALS'):
                print("Using FIREBASE_CREDENTIALS environment variable")
                cred_dict = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
                cred = credentials.Certificate(cred_dict)
            else:
                print("No Firebase credentials found!")
                raise Exception("No Firebase credentials found")
            
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully")
            return firestore.client()
        except Exception as e:
            print(f"Firebase initialization error: {str(e)}")
            print(f"Error type: {type(e)}")
            if os.getenv('FIREBASE_CREDENTIALS'):
                print("FIREBASE_CREDENTIALS environment variable exists")
            return None
    return firestore.client()

@app.route('/')
def index():
    firebase_config = get_firebase_config()
    print("Firebase Config for client:", firebase_config)  # Debug log
    return render_template('index.html', firebase_config=firebase_config)

@app.route('/login')
def login():
    firebase_config = get_firebase_config()
    print("Firebase Config for login:", firebase_config)  # Debug log
    return render_template('login.html', firebase_config=firebase_config)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    try:
        print("Starting token verification...")
        id_token = request.json.get('idToken')
        if not id_token:
            print("No token provided in request")
            return jsonify({"error": "No token provided"}), 400

        print("Attempting to verify token...")
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            print("Firebase not initialized, initializing now...")
            db = init_firebase()
            if not db:
                print("Failed to initialize Firebase")
                return jsonify({"error": "Firebase initialization failed"}), 500

        # Verify the Firebase ID token
        try:
            decoded_token = auth.verify_id_token(id_token)
            print(f"Token verified successfully. User ID: {decoded_token['uid']}")
            uid = decoded_token['uid']
            email = decoded_token.get('email', '')
        except Exception as token_error:
            print(f"Token verification failed: {str(token_error)}")
            return jsonify({"error": f"Token verification failed: {str(token_error)}"}), 401

        # Create user and log them in
        user = User(uid, email)
        login_user(user)
        print(f"User logged in successfully: {email}")
        
        return jsonify({"message": "Successfully logged in"}), 200
    except Exception as e:
        print(f"Unexpected error in verify_token: {str(e)}")
        return jsonify({"error": str(e)}), 401

@app.route('/api/subscribe', methods=['POST'])
@login_required
def subscribe():
    try:
        db = init_firebase()
        if not db:
            return jsonify({"error": "Firebase not initialized"}), 500

        data = request.json
        email = data.get('email')
        name = data.get('name', '')
        
        if not email:
            return jsonify({"error": "Email is required"}), 400

        # Store in Firestore
        doc_ref = db.collection('subscribers').document()
        doc_ref.set({
            'email': email,
            'name': name,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'active',
            'user_id': current_user.id
        })

        return jsonify({"message": "Successfully subscribed"}), 200

    except Exception as e:
        print(f"Subscription error: {e}")
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

@app.route('/subscribers')
@login_required
def subscribers_page():
    try:
        db = init_firebase()
        if not db:
            return "Failed to initialize Firebase", 500
        
        # Fetch all subscribers
        subscribers = []
        docs = db.collection('subscribers').stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id  # Add document ID
            subscribers.append(data)
        
        return render_template('subscribers.html', subscribers=subscribers)
    except Exception as e:
        print(f"Error fetching subscribers: {e}")
        return str(e), 500

# Required for Vercel
app.debug = os.getenv('DEBUG', 'False').lower() == 'true'

# This is important for Vercel
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 