from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import secrets
import pytz
timezone = pytz.timezone("Europe/Paris")
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

    def create_user(self, username:str ,email:str, password:str, first_name:str, last_name:str, hire_date:str, birth_date:str, Position:float = [0,0]):
        max_length = 50
        max_length_name = 10
        max_length_password = 160
        username = username[:max_length]
        email = email[:max_length]
        password = password[:max_length_password]
        first_name = first_name[:max_length_name]
        last_name = last_name[:max_length_name]
        Position = Position

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
            "birth_date": datetime.strptime(birth_date, '%Y-%m-%d'),
            "Position": Position,
        }
        return self.create(user_data)


class Trip(BaseModel):
    def __init__(self, db):
        super().__init__(db, "trip")
    def create_trip(self, user_id: str, start_date: str, end_date: str, position_dot: int, Is_done: bool, distance: int):
        max_distance = 1100  # Example maximum distance
        distance = min(distance, max_distance)
        position_dot = min(int(position_dot), 100)  # Convert position_dot to int before comparison

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
            "position_dot": position_dot,
            "Is_done": Is_done,
            "distance": distance
        }
        return self.create(trip_data)

class API_KEY(BaseModel):
    def __init__(self, db):
        super().__init__(db, "api_key")
    def generate_api_key(self, user_id: str):
        #to check if the user already has an api key
        check_user = self.read_one({"user_id": ObjectId(user_id)})
        if check_user:
            return check_user["key"]
        else:
            # Generate a secure, random key using the secrets module
            key = secrets.token_urlsafe(32)  # Generates a 32-byte (256-bit) key
            # Truncate or format the key if necessary (optional)
            # key = key[:50]  # Example: Truncate to 50 characters if needed
            # Create the API key in the database with an expiration time
            expiration_time = datetime.now() + timedelta(days=1)  # Set expiration to 1 day from now
            
            key_data = {
                "key": key,
                "expiration_time": expiration_time  # Set expiration to 1 day from now
            }
            self.create(key_data)
            return key
        
    def is_api_key_valid(self, key:str):
        
     result = self.read_one({"key": key})
     print(f"Debug: read_one result for key '{key}': {result}")  # Debugging line
     if result:
        return True
     else:
        return False
    
class relay_point(BaseModel):
    def __init__(self, db):
        super().__init__(db, 'relay_point')
    def create_relay_point(self, name:str, location:int):
       if self.dedublicate_relay_check(name):
           return False
       else:
        max_length = 50
        name = name[:max_length]
        location = location
       
        relay_point_data = {
            "location": location,
            
        }
        return self.create(relay_point_data)
    def dedublicate_relay_check(self, location:str):
        result = self.read_one({"location": location})
        if result:
            return True
        else:
            return False