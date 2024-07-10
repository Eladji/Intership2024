from flask import request, jsonify
from app import app, mongo
from app.Model import User
from bson.objectid import ObjectId
from datetime import datetime

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    required_fields = ["email", "password", "first_name", "last_name", "car_ids", "hire_date", "birth_date"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400
    
    user = User(mongo.db)
    user.create_user(
        email=data["email"],
        password=data["password"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        car_ids=data["car_ids"],
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
        user['car_ids'] = [str(car_id) for car_id in user['car_ids']]
        result.append(user)
    return jsonify(result), 200

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = User(mongo.db)
    update_data = {key: value for key, value in data.items() if key in ["email", "password", "first_name", "last_name", "car_ids", "hire_date", "birth_date"]}
    if 'car_ids' in update_data:
        update_data['car_ids'] = [ObjectId(car_id) for car_id in update_data['car_ids']]
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
