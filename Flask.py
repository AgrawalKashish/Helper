from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app)

# JWT config
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # 🔒 use env variable in production
jwt = JWTManager(app)

# --- Signup route ---
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    uid = data.get('uid')
    password = data.get('password')
    name = data.get('name')
    dob = data.get('dob')
    contact = data.get('contact')

    if mongo.db.users.find_one({"uid": uid}):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = generate_password_hash(password)

    mongo.db.users.insert_one({
        "uid": uid,
        "password": hashed_pw,
        "name": name,
        "dob": dob,
        "contact": contact
    })

    return jsonify({"message": "Signup successful"}), 201

# --- Login route (returns JWT token) ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    uid = data.get('uid')
    password = data.get('password')

    user = mongo.db.users.find_one({"uid": uid})

    if user and check_password_hash(user['password'], password):
        # Generate token with user id
        access_token = create_access_token(identity=uid)
        return jsonify({"token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# --- Protected route (requires token) ---
@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()  # uid stored in token
    user = mongo.db.users.find_one({"uid": current_user}, {"_id": 0, "password": 0})

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"profile": user}), 200


if __name__ == '__main__':
    app.run(debug=True)
