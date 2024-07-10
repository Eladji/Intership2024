from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

class BaseModel:
    def __init__(self, db, collection_name):
        self.collection = db[collection_name]

    def create(self, data):
        return self.collection.insert_one(data)

    def read(self, query):
        return self.collection.find(query)

    def read_one(self, query):
        return self.collection.find_one(query)

    def update(self, query, data):
        return self.collection.update_one(query, {"$set": data})

    def delete(self, query):
        return self.collection.delete_one(query)

class User(BaseModel):
    def __init__(self, db):
        super().__init__(db, "users")

    def create_user(self, email, password, first_name, last_name, hire_date, birth_date):
        user_data = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "hire_date": datetime.strptime(hire_date, '%Y-%m-%d'),
            "birth_date": datetime.strptime(birth_date, '%Y-%m-%d')
        }
        return self.create(user_data)


class Trip(BaseModel):
    def __init__(self, db):
        super().__init__(db, "trip")
    def create_trip(self, user_id,  start_date, end_date, position_dot, Is_done, distance):
        
        trip_data = {
            "user_id": ObjectId(user_id),
            "start_date": datetime.strptime(start_date, '%Y-%m-%d'),
            "end_date": datetime.strptime(end_date, '%Y-%m-%d'),
            "position_dot" : position_dot,
            "Is_done": Is_done,
            "distance": distance
        }
        return self.create(trip_data)