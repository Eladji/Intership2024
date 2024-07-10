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

    def create_user(self, username:str ,email:str, password:str, first_name:str, last_name:str, hire_date:str, birth_date:str):
        max_length = 50
        max_length_name = 10
        max_length_password = 160
        username = username[:max_length]
        email = email[:max_length]
        password = password[:max_length_password]
        first_name = first_name[:max_length_name]
        last_name = last_name[:max_length_name]

        # Convert strings to datetime, ensuring they are not in the future
        now = datetime.now()
        hire_date_dt = min(datetime.strptime(hire_date, '%Y-%m-%d-%H:%M'), now)
        birth_date_dt = datetime.strptime(birth_date, '%Y-%m-%d')

        user_data = {
            "username": username,
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "hire_date": datetime.strptime(hire_date, '%Y-%m-%d-%H:%M'),
            "birth_date": datetime.strptime(birth_date, '%Y-%m-%d')
        }
        return self.create(user_data)


class Trip(BaseModel):
    def __init__(self, db):
        super().__init__(db, "trip")
    def create_trip(self, user_id: str,  start_date:str, end_date: str, position_dot: int, Is_done: bool, distance: int):
        max_distance = 1100  # Example maximum distance
        distance = min(distance, max_distance)
        position_dot = min(position_dot, 100)  # Example maximum for position_dot

        # Convert strings to datetime, ensuring start_date is before end_date and neither are in the future
        now = datetime.now()
        start_date_dt = min(datetime.strptime(start_date, '%Y-%m-%d-%H:%M:%S'), now)
        end_date_dt = min(datetime.strptime(end_date, '%Y-%m-%d-%H:%M:%S'), now)
        if end_date_dt < start_date_dt:
            end_date_dt = start_date_dt
        trip_data = {
            "user_id": ObjectId(user_id),
            "start_date": datetime.strptime(start_date, '%Y-%m-%d-%H:%M:%S'),
            "end_date": datetime.strptime(end_date, '%Y-%m-%d-%H:%M:%S'),
            "position_dot" : position_dot,
            "Is_done": Is_done,
            "distance": distance
        }
        return self.create(trip_data)