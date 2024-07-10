import urllib.parse
from  dotenv import load_dotenv
import os   
from flask.app import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)
load_dotenv()
mongo_user = urllib.parse.quote_plus(os.getenv("MONGO_INITDB_ROOT_USERNAME"))
mongo_password = urllib.parse.quote_plus(os.getenv("MONGO_INITDB_ROOT_PASSWORD")) 
app.config["MONGO_URI"] = "mongodb://mongo:27017/mydatabase"

mongo = PyMongo(app)

from app import routes
