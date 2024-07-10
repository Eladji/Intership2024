from flask import request, jsonify, abort
from app import app, mongo
from app.Model import User, Trip
from bson.objectid import ObjectId
from datetime import datetime

VALID_API_KEYS = {"qb9luXtdMCqR7Bqy"}  # Define your valid API keys

@app.before_request
def require_api_key():
    if 'X-API-KEY' not in request.headers or request.headers['X-API-KEY'] not in VALID_API_KEYS:
        # If the API key is missing or not valid, return an unauthorized error
        abort(jsonify({"error": "Unauthorized"}), 401)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    required_fields = ["email", "password", "first_name", "last_name", "hire_date", "birth_date"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400
    
    user = User(mongo.db)
    user.create_user(
        email=data["email"],
        password=data["password"],
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

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = User(mongo.db)
    update_data = {key: value for key, value in data.items() if key in ["email", "password", "first_name", "last_name", "hire_date", "birth_date"]}

    if 'hire_date' in update_data:
        update_data['hire_date'] = datetime.strptime(update_data['hire_date'], '%Y-%m-%d')
    if 'birth_date' in update_data:
        update_data['birth_date'] = datetime.strptime(update_data['birth_date'], '%Y-%m-%d')
    user.update({"_id": ObjectId(user_id)}, update_data)
    return jsonify({"message": "User updated"}), 200

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User(mongo.db)
    user.delete({"_id": ObjectId(user_id)})
    return jsonify({"message": "User deleted"}), 200



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