"""
Firebase configuration module.
Client-side configuration is stored here as it's public anyway in the web client.
Server-side credentials should be stored in environment variables.
"""

# Web Client Firebase Configuration
FIREBASE_WEB_CONFIG = {
    "apiKey": "AIzaSyAXLKyKue10uBRenJvsC81GYQDl0eVXYHc",
    "authDomain": "vibe-coding-cursor.firebaseapp.com",
    "projectId": "vibe-coding-cursor",
    "storageBucket": "vibe-coding-cursor.firebasestorage.app",
    "messagingSenderId": "1048387694267",
    "appId": "1:1048387694267:web:a8750e49028e815d47c39e"
}

# Function to get Firebase configuration
def get_firebase_config():
    return FIREBASE_WEB_CONFIG 