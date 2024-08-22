from flask import request, jsonify, abort, send_file
from app import app, mongo
from app.Model import User, Trip, API_KEY
from bson.objectid import ObjectId
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from ml_model import generate_relay_points
CORS(app)
bcrypt = Bcrypt(app)
@app.before_request
def require_api_key():
    open_endpoints = ['login', 'register', 'map', 'get_map','relay_points/generate','relay_points']
    if request.endpoint in open_endpoints:
        return  # Allow the request for open endpoints
    if 'X-API-KEY' in request.headers:
        apikey = API_KEY(mongo.db)
        if apikey.is_api_key_valid(request.headers['X-API-KEY']):
            return  # Allow the request if the API key is valid
        else:
            abort(jsonify({"error": "Unauthorized"}), 401)  # Abort if the API key is invalid
    else:
        abort(jsonify({"error": "Unauthorized"}), 401)  # Abort if the API key is missing
        
@app.route('/login', methods=['POST'], endpoint='login')
def login():
    data = request.get_json()
    required_fields = ["email", "password"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400
    user = User(mongo.db)
    user_data = user.read_one({"email": data["email"]})
    
    if user_data and bcrypt.check_password_hash(user_data["password"], data["password"]):
        apikey = API_KEY(mongo.db)
        user_data['_id'] = str(user_data['_id'])
        user_data.pop("password")  # Corrected from user_data.pop["password"]
        # Correctly add API_KEY and message to the user_data dictionary
        user_data["API_KEY"] = apikey.generate_api_key(user_data["_id"])  # Corrected from user_data.append[{"API_KEY": apikey.generate_api_key()}]
        user_data["message"] = "User logged in"  # Corrected from user_data.append[{"message": "User logged in"}]
        return jsonify(user_data), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/register', methods=['POST'], endpoint='register')
def create_user():
    data = request.get_json()
    required_fields = ["email", "password", "first_name", "last_name", "hire_date", "birth_date", "username"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400
    
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
    
    user = User(mongo.db)
    #check if email or username already exists
    if (user.read_one({"email": data["email"]})):
        return jsonify({"error": "Email already exists"}), 400
    if (user.read_one({"username": data["username"]})):
        return jsonify({"error": "Username already exists"}), 400
    
    user.create_user(
        email=data["email"],
        password=hashed_password,
        username=data["username"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        hire_date=data["hire_date"],
        birth_date=data["birth_date"]
    )
    return jsonify({"message": "User created"}), 201

@app.route('/users', methods=['GET'])
def get_users():
    user = User(mongo.db)
    users = user.read({})
    result = []
    for user in users:
        user['_id'] = str(user['_id'])
        result.append(user)
    return jsonify(result), 200

@app.route('/users/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = User(mongo.db)
    user = user.read_one({"_id": ObjectId(user_id)})
    user['_id'] = str(user['_id'])
    return jsonify(user), 200

@app.route('/users/<username>', methods=['GET'])
def get_user_by_username(username):
    user = User(mongo.db)
    user = user.read_one({"username": username})
    user['_id'] = str(user['_id'])
    return jsonify(user), 200

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = User(mongo.db)
    update_data = {key: value for key, value in data.items() if key in ["email", "password", "first_name", "last_name", "hire_date", "birth_date"]}

    if 'hire_date' in update_data:
        update_data['hire_date'] = datetime.strptime(update_data['hire_date'], '%Y-%m-%d-%H:%M')
    if 'birth_date' in update_data:
        update_data['birth_date'] = datetime.strptime(update_data['birth_date'], '%Y-%m-%d')
    user.update({"_id": ObjectId(user_id)}, update_data)
    return jsonify({"message": "User updated"}), 200

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User(mongo.db)
    user.delete({"_id": ObjectId(user_id)})
    return jsonify({"message": "User deleted"}), 200

@app.route('/map')
def get_map():
    return send_file('relay_points_map.html'), 200


@app.route('/trips', methods=['POST'])
def create_trip():
    data = request.get_json()
    required_fields = ["user_id", "start_date", "end_date", "position_dot", "Is_done", "distance"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400
    
    trip = Trip(mongo.db)
    trip.create_trip(
        user_id=data["user_id"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        position_dot=data["position_dot"],
        Is_done=data["Is_done"],
        distance=data["distance"]
    )
    return jsonify({"message": "Trip created"}), 201

@app.route('/trips/<user_id>', methods=['GET'])
def get_trips(user_id):
    trip = Trip(mongo.db)
    user = User(mongo.db)
    if user.read_one({"_id": ObjectId(user_id)}):
        trips = trip.read({})

        result = []
        for trip in trips:
            # Convert ObjectId to string for JSON serialization
            trip["_id"] = str(trip['_id'])
            trip["user_id"] = str(trip["user_id"])
            # If there are other ObjectId fields, convert them to strings as well
            # Example: trip['user_id'] = str(trip['user_id'])
            result.append(trip)
        return jsonify(result), 200
    else:
        return jsonify({"error": "invalid user id"}), 404

@app.route('/trips/<trip_id>', methods=['PUT'])
def update_trip(trip_id):
    data = request.get_json()
    trip = Trip(mongo.db)
    update_data = {key: value for key, value in data.items() if key in ["user_id", "start_date", "end_date", "position_dot", "Is_done", "distance"]}
    if 'user_id' in update_data:
        update_data['user_id'] = ObjectId(update_data['user_id'])
   
    if 'start_date' in update_data:
        update_data['start_date'] = datetime.strptime(update_data['start_date'], '%Y-%m-%d')
    if 'end_date' in update_data:
        update_data['end_date'] = datetime.strptime(update_data['end_date'], '%Y-%m-%d')
    trip.update({"_id": ObjectId(trip_id)}, update_data)
    return jsonify({"message": "Trip updated"}), 200
@app.route('/trips/<trip_id>', methods=['DELETE'])
def delete_trip(trip_id):
    trip = Trip(mongo.db)
    trip.delete({"_id": ObjectId(trip_id)})
    return jsonify({"message": "Trip deleted"}), 200

@app.route('/relay_points', methods=['GET'])
def get_relay_points():
    relay_points = mongo.db.relay_points.find({})
    result = []
    for point in relay_points:
        point['_id'] = str(point['_id'])
        result.append(point)
    return jsonify(result), 200

@app.route('/relay_points/generate', methods=['POST'])
def generate_relay():
    relay_points = generate_relay_points()
    if relay_points:
        return jsonify({"message": "Relay points generated"}), 200
    else:
        return jsonify({"error": "Error generating relay points"}), 500