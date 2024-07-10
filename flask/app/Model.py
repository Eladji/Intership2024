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

    def create_user(self, email, password, first_name, last_name, car_ids, hire_date, birth_date):
        user_data = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "car_ids": [ObjectId(car_id) for car_id in car_ids],
            "hire_date": datetime.strptime(hire_date, '%Y-%m-%d'),
            "birth_date": datetime.strptime(birth_date, '%Y-%m-%d')
        }
        return self.create(user_data)
