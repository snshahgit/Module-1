from flask import Flask, request, jsonify
from pymongo.errors import DuplicateKeyError
from mongodb_connection import get_database

app = Flask(__name__)

@app.route('/add_properties', methods=['POST'])
def add_properties():
    data = request.json
    print("Adding data to db")
    if not data:
        return jsonify({"error": "No data provided"}), 400
    db = get_database()
    properties_collection = db.Properties
    inserted_ids = []
    for property_data in data:
        try:
            result = properties_collection.update_one(
                {"address": property_data["address"]},  # Find the document by address
                {"$set": property_data},  # Update the document with new data
                upsert=True  # Insert the document if it doesn't exist
            )
            if result.upserted_id is not None:
                inserted_ids.append(str(result.upserted_id))
            else:
                inserted_ids.append(f"Updated property: {property_data['address']}")
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"inserted_or_updated": inserted_ids}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
