from pymongo.server_api import ServerApi
from pymongo import MongoClient
from threading import Lock

class MongoDBClient:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    uri = "mongodb+srv://bhavikkshah33:root@cluster0.15gd3y0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
                    cls._instance = MongoClient(uri, server_api=ServerApi('1'))
        return cls._instance

def get_database():
    client = MongoDBClient()
    db = client.Real_Estate
    db.Properties.create_index([("address", 1)], unique=True)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"An error occurred: {e}")
    return db
