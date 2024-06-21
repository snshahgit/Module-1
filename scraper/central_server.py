from flask import Flask, request, jsonify
from pymongo import MongoClient
from mongodb_connection import get_database

app = Flask(__name__)

@app.route('/add_properties', methods=['POST'])
def add_properties():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    db = get_database()
    properties_collection = db.properties
    try:
        result = properties_collection.insert_many(data)
        return jsonify({"inserted_ids": str(result.inserted_ids)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
