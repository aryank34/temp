from bson import ObjectId
from flask import Flask, jsonify, make_response
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv, find_dotenv

# Create a new Flask web server instance
app = Flask(__name__)

# Load environment variables from a .env file
load_dotenv(find_dotenv())

# Get the MongoDB host URI from environment variables
mongo_host = os.environ.get("MONGO_HOST_prim")

# Function to check the connection to the MongoDB server
def dbConnectWorkBaseCheck():
    try:
        # Create a new MongoDB client
        uri = mongo_host
        client = MongoClient(uri, server_api=ServerApi('1'))

        # Ping the MongoDB server to check the connection
        client.WorkBaseDB.command('ping')

        # Return the client if the connection is successful
        return client
    except Exception as e:
        # Return an error response if the connection fails
        return make_response(jsonify({"error": str(e)}), 500)

# Function to determine the user type based on the account ID
def userType(account_id):
    try: 
        # Check the connection to the MongoDB server
        client = dbConnectWorkBaseCheck()

        # If the connection is successful
        if isinstance(client, MongoClient):
            # Access the 'Projects' collection
            user_collection = client.WorkBaseDB.Members
            # Check if the account ID exists in the collection
            account_exists = user_collection.find_one({"_id": ObjectId(account_id)})
            if not account_exists:
                return make_response(jsonify({"error": "Account ID does not exist"}), 404)

            manager_project = client.WorkBaseDB.Projects
            # Find a document where the 'managerID' field matches the account ID
            isManager = manager_project.find_one({"managerID": ObjectId(account_id)}) 
            # If a document is found, the user is a manager
            if isManager:
                return make_response(jsonify({"userType": 'manager'}), 200)  
            else:
                # If no document is found, the user is an employee
                return make_response(jsonify({"userType": 'employee'}), 200)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

