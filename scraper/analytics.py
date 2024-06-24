from pymongo.server_api import ServerApi
from pymongo import MongoClient
import pymysql
import re
import json

# MongoDB connection details
uri = "mongodb+srv://bhavikkshah33:root@cluster0.15gd3y0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["Real_Estate"]
collection = db["Properties_New"]

# PostgreSQL RDS connection details
rds_host = "hackathon.c56geukiivra.us-east-1.rds.amazonaws.com"
rds_port = 3306
rds_dbname = "hackathonDB"
rds_user = "admin"
rds_password = "shahsaumya"

try:
    conn = pymysql.connect(
        host=rds_host,
        port=rds_port,
        db=rds_dbname,
        user=rds_user,
        password=rds_password,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS Properties;")
    conn.commit()

    cursor.execute("DROP TABLE IF EXISTS Features;")
    conn.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Properties (
            id VARCHAR(255) PRIMARY KEY,
            pin CHAR(5),
            houseType TEXT,
            address TEXT,
            price REAL,
            beds REAL,
            baths REAL,
            sqft REAL,
            parking REAL,
            construction INTEGER,
            pricePerSqft REAL,
            homeOwnersAssociationFees REAL,
            tax REAL,
            taxYear INTEGER,
            imgUrls TEXT
        );
    ''')
    conn.commit()


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Features (
            id VARCHAR(255) PRIMARY KEY,
            safety REAL,
            schoolCount INTEGER,
            sideWalkScore INTEGER,
            transitScore INTEGER,
            weatherScore INTEGER,
            weatherRisks TEXT
        );
    ''')
    conn.commit()


    def extract_tax_value(tax_info):
        if tax_info:
            match = re.search(r'\$([\d,]+(?:\.\d{1,2})?)', tax_info)
            if match:
                return float(match.group(1).replace(',', ''))
        return None
    
    def get_weatherScore(docs):
        weatherScore=10
        for doc in docs:
            if "severe" in doc.lower():
                weatherScore-=2
            elif "major" in doc.lower():
                weatherScore-=1
        return weatherScore
    
    def get_weatherRisks(docs):
        weatherRisks = []
        for doc in docs:
            weatherRisks.append(doc.split(" ")[0])
        return weatherRisks


    documents = collection.find()

    for document in documents:
        try:
            data = {
                "id": str(document.get("_id")),
                "pin": str(document.get("pin")),
                "houseType": document.get("houseType"),
                "address": document.get("address"),
                "price": float(document.get("price").replace("$", "").replace(",", "").replace(".", "")),
                "beds": float(document.get("beds")) if document.get("beds") else None,
                "baths": float(document.get("baths")) if document.get("baths") else None,
                "sqft": float(document.get("sqft").replace(",", "")) if (document.get("sqft") and document.get("sqft") != '—') else 0,
                "parking": float(re.sub(r'[^\d.]', '', document.get("parking", "0"))) if document.get("parking") else 0,
                "construction": int(re.search(r'\d+', document.get("construction", "0")).group()) if document.get("construction") and re.search(r'\d{4}', document.get("construction", "")) else None,
                "pricePerSqft": float(document.get("pricePerSqft").replace("$", "").replace(",", "").replace(" per sq ft", "")) if (document.get("pricePerSqft") and re.search(r'\d+', document.get("pricePerSqft", ""))) else None,
                "homeOwnersAssociationFees": float(document.get("homeOwnersAssociationFees").replace("$", "").replace(",", "").replace(" monthly HOA fee", ""))if (document.get("homeOwnersAssociationFees") and re.search(r'\d+', document.get("homeOwnersAssociationFees", "0"))) else None,
                "tax": extract_tax_value(document.get("taxInfo", "")),
                "taxYear": int(re.search(r'\d{4}', document.get("taxInfo", "")).group()) if document.get("taxInfo") and re.search(r'\d{4}', document.get("taxInfo", "")) else None,
                "imgUrls": ",".join(document.get("imgUrls", [])),
                "safety": round(float(document.get("safety")),2) if document.get("safety") else 0,
                "schoolCount": int(document.get("schoolCount")) if (document.get("schoolCount") and re.search(r'\d+', document.get("schoolCount", ""))) else 0,
                "sideWalkScore": int(document.get("sideWalkScore")[:-4]) if (document.get("sideWalkScore") and re.search(r'\d+', document.get("sideWalkScore", ""))) else 0,
                "transitScore": int(document.get("transitScore")[:-4]) if (document.get("transitScore") and re.search(r'\d+', document.get("transitScore", ""))) else 0,
                "weatherScore": get_weatherScore(document.get("weather")) if document.get("weather") else 5,
                "weatherRisks": json.dumps(get_weatherRisks(document.get("weather")) if document.get("weather") else ["moderate"]*5)
                
            }


            cursor.execute('''
                INSERT INTO Properties (
                    id, pin, houseType, address, price, beds, baths, sqft, parking, construction,
                    pricePerSqft, homeOwnersAssociationFees, tax, taxYear, imgUrls
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                data["id"], data["pin"], data["houseType"], data["address"], data["price"], data["beds"], data["baths"],
                data["sqft"], data["parking"], data["construction"], data["pricePerSqft"], data["homeOwnersAssociationFees"],
                data["tax"], data["taxYear"], data["imgUrls"]
            ))
            conn.commit()

            cursor.execute('''
                INSERT INTO Features (
                    id, safety, schoolCount, sideWalkScore, transitScore, weatherScore, weatherRisks
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                data["id"], data["safety"], data["schoolCount"], data["sideWalkScore"], data["transitScore"], data["weatherScore"], data["weatherRisks"]
            ))
            conn.commit()

        except Exception as e:
            print(f"An error occurred with document {document.get('_id')}: {e}")

    print("Data insertion completed successfully.")

finally:
    if 'conn' in locals() and conn.open:
        conn.close()
    if 'mongo_client' in locals():
        client.close()