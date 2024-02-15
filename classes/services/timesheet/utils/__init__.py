from bson import ObjectId
from flask import Flask, jsonify, make_response
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv, find_dotenv
from bson.binary import UuidRepresentation
from uuid import UUID

# Create a new Flask web server instance
app = Flask(__name__)

# Load environment variables from a .env file
load_dotenv(find_dotenv())

# Get the MongoDB host URI from environment variables
mongo_host = os.environ.get("MONGO_HOST_prim")

def get_WorkAccount(client, uid):
    """
    This function retrieves the account details of a user from the database.
    It takes a MongoClient instance and a user ID as input.
    It returns the account details if the user ID exists, or an error response if it does not exist or if an error occurs.
    """
    try:
        # Access the 'employeeData' collection
        employeeData_collection = client.sample_employee.employeeData
        # Check if the user ID exists in the collection
        user_accountID = employeeData_collection.find_one({"id": UUID(uid)}, {"_id": 1})
        # return make_response(jsonify({"message": "working"}), 200)
        # Access the 'Members' collection
        members_collection = client.WorkBaseDB.Members
        user_account = members_collection.find_one({"employeeDataID": ObjectId(user_accountID["_id"])}, {"_id": 1})
 
        # If the user ID does not exist, return an error response
        if not user_account:
            return make_response(jsonify({"error": "User ID does not exist"}), 404)
       
        # If the user ID exists, return the account details
        return make_response(jsonify({"_id": str(user_account["_id"])}), 200)
 
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

# Function to check the connection to the MongoDB server
def dbConnectWorkBaseCheck():
    try:
        # Create a new MongoDB client
        uri = mongo_host
        client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")

        # Ping the MongoDB server to check the connection
        client.WorkBaseDB.command('ping')

        # Return the client if the connection is successful
        return client
    except Exception as e:
        # Return an error response if the connection fails
        return make_response(jsonify({"error": str(e)}), 500)

# Function to determine the user type based on the account ID
def userType(account_uuid):
    try: 
        # Check the connection to the MongoDB server
        client = dbConnectWorkBaseCheck()
        
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

