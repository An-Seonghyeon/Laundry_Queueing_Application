from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase Admin
cred = credentials.Certificate("hd-laundry-qr-firebase-adminsdk-jk05n-e56796e24b.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def home():
    return "Welcome to the Firebase Flask app!"

@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        data = request.json
        # Add a new document
        ref = db.collection('users').add(data)
        return jsonify({"success": True, "id": ref[1].id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        # Get all users from the Firestore collection
        users_ref = db.collection('users').stream()
        users = [{doc.id: doc.to_dict()} for doc in users_ref]
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)