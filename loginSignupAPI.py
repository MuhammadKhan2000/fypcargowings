from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt

# Initialize Flask app
app = Flask(__name__)

# MongoDB client setup
client = MongoClient('mongodb://localhost:27017')
db = client['CargoTracking']
users_collection = db['users']

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Helper function to verify passwords
def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

# Route for user sign-up
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Check if the user already exists
    if users_collection.find_one({'username': username}):
        return jsonify({'message': 'User already exists'}), 400

    # Insert new user into the database
    hashed_pw = hash_password(password)
    user_id = users_collection.insert_one({'username': username, 'password': hashed_pw}).inserted_id

    return jsonify({'message': 'User registered successfully', 'user_id': str(user_id)}), 201

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Find the user in the database
    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'message': 'Invalid username or password'}), 401

    # Verify the password
    if not check_password(user['password'], password):
        return jsonify({'message': 'Invalid username or password'}), 401

    return jsonify({'message': 'Login successful', 'user_id': str(user['_id'])}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
