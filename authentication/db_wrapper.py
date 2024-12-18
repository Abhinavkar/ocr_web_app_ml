from pymongo import MongoClient

# MongoDB Configuration
MONGO_URI = "mongodb+srv://ritu:12345@model.5hsae.mongodb.net/?retryWrites=true&w=majority&appName=model"
MONGO_DB_NAME = "ocr_db"

# Initialize MongoDB Client
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

def get_collection(collection_name):
    """
    Returns a MongoDB collection.
    """
    return db[collection_name]
