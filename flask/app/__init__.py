import urllib.parse
from  dotenv import load_dotenv
import os   
from flask.app import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)
load_dotenv()
mongo_user = urllib.parse.quote_plus(os.getenv("MONGO_INITDB_ROOT_USERNAME"))
mongo_password = urllib.parse.quote_plus(os.getenv("MONGO_INITDB_ROOT_PASSWORD")) 
app.config["MONGO_URI"] = "mongodb://mongo:27017/Saint-Bernard"


mongo = PyMongo(app)

from app import routes
def init_db(app):
    mongo = PyMongo(app)
    db = mongo.db

    # Create initial collections and indexes if they don't exist
    try:
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
            print("Created 'users' collection")
            db.users.create_index("username", unique=True)
            db.users.create_index("email", unique=True)
            db.users.create_index("hire_date")
            db.users.create_index("birth_date")
            db.users.create_index("first_name")
            db.users.create_index("last_name")
            db.users.create_index("password")
            db.users.create_index("Position")
   
        if 'trip' not in db.list_collection_names():
            db.create_collection('trip')
            print("Created 'trip' collection")
            
            db.trip.create_index("user_id")
            db.trip.create_index("start_date")
            db.trip.create_index("end_date")
            db.trip.create_index("position_dot")
            db.trip.create_index("Is_done")
            db.trip.create_index("distance")
            
        if 'api_key' not in db.list_collection_names():
            db.create_collection('api_key')
            db.key.create_index("key", unique=True)
            db.key.create_index("user_id")
            db.key.create_index("expiration_time", expireAfterSeconds=86400 )
            print("Created 'key' collection")
            
        if 'relay_points' not in db.list_collection_names():
            db.create_collection('relay_points')
            print("Created 'relay_points' collection")
            db.relay_points.create_index("location")
         
            
    except Exception as e:
        print("Error initializing database:", e)
    return    print("Database initialized")
init_db(app)
