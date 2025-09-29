import os
from flask import Flask
from flask_pymongo import PyMongo
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

app = Flask(__name__)

# Build Mongo URI from environment variables
mongo_uri = (
    f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}"
    f"@{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}/"
    f"{os.getenv('MONGO_DB')}?authSource={os.getenv('MONGO_AUTHSOURCE')}"
    f"&authMechanism={os.getenv('MONGO_AUTHMECH')}"
)

app.config["MONGO_URI"] = mongo_uri

mongo = PyMongo(app)

# JWT Secret Key
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
