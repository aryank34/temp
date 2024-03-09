from uuid import UUID
from bson import ObjectId
from flask import jsonify, make_response
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import find_dotenv, load_dotenv
# Load environment variables from a .env file
load_dotenv(find_dotenv())

# Get the MongoDB host URI from environment variables
mongo_host = os.environ.get("MONGO_HOST_prim")

def dbConnectCheck():
    """
    This function creates a new MongoDB client and checks the connection to the MongoDB server.
    It returns the MongoClient instance if the connection is successful, or an error response if the connection fails.
    """
    try:
        # Create a new MongoDB client
        uri = mongo_host
        client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")

        # Return the client if the connection is successful
        return client

    except Exception as e:
        # Return an error response if the connection fails
        return make_response(jsonify({"error": str(e)}), 500)
    
def get_WorkAccount(client, uid):
    """
    This function retrieves the account details of a user from the database.
    It takes a MongoClient instance and a user ID as input.
    It returns the account details if the user ID exists, or an error response if it does not exist or if an error occurs.
    """
    try:
        # Access the 'employeeData' collection
        employeeData_collection = client.EmployeeDB.employeeData
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
    
def verify_attribute(collection, key, attr_value):
    """
    This function checks if an account ID exists in the 'Members' collection of the database.
    It takes a MongoClient instance and an account ID as input.
    It returns True if the account ID exists, or an error response if it does not exist or if an error occurs.
    """
    try:
        # # Access the 'Members' collection
        # user_collection = collection.WorkBaseDB.Members
        # Check if the account ID exists in the collection
        account_exists = collection.find_one({key: attr_value})

        # If the account ID does not exist, return an error response
        if not account_exists:
            return make_response(jsonify({"error": "Account ID does not exist"}), 404)
        return make_response(jsonify({"message": "Account ID exists"}), 200)

    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)
    
def isSuperAdmin(account_uuid):
    """
    This function checks if the user is a super admin.
    It takes a user ID as input.
    It returns True if the user is a super admin, or an error response if the user is not a super admin or if an error occurs.
    """
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()

        if isinstance(client, MongoClient):

            # correct data field formats for timesheet
            # check if the managerID is valid
            verify = get_WorkAccount(client, account_uuid)
            if not verify.status_code == 200:
                # If the connection fails, return the error response
                return verify
            account_id= verify.json['_id']

            response = client.WorkBaseDB.Members.find_one({"_id": ObjectId(account_id), "superAdmin": True})
            if response:
                return make_response(jsonify({"response": True}), 200)
            else:
                return make_response(jsonify({"response": False}), 200)

        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)

    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)