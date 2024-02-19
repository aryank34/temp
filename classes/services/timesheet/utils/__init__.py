from bson import ObjectId
from flask import Flask, jsonify, make_response
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv, find_dotenv
from bson.binary import UuidRepresentation
from uuid import UUID

from ...connectors.dbConnector import dbConnectCheck, get_WorkAccount

# Create a new Flask web server instance
app = Flask(__name__)

# Load environment variables from a .env file
load_dotenv(find_dotenv())

# Get the MongoDB host URI from environment variables
mongo_host = os.environ.get("MONGO_HOST_prim")

# Function to determine the user type based on the account ID
def userType(account_uuid):
    try: 
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        
        verify = get_WorkAccount(client, account_uuid)
        if not verify.status_code == 200:
            # If the connection fails, return the error response
            return verify
        account_id = verify.json['_id']
        
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

