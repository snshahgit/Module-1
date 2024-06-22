from pymongo.server_api import ServerApi
from pymongo import MongoClient

def get_mongo_client():
    uri = "mongodb+srv://bhavikkshah33:root@cluster0.15gd3y0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    return client

def create_unique_index(db):
    db.Properties.create_index([("address", 1)], unique=True)

def get_database():
    client = get_mongo_client()
    db= client.Real_Estate
    create_unique_index(db)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"An error occurred: {e}")
    # Return the Real_Estate database
    return db
