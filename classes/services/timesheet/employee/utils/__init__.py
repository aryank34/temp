# Import necessary modules
from bson import ObjectId
from bson.binary import UuidRepresentation
from uuid import UUID
from flask import Flask, jsonify, make_response
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv, find_dotenv
import json


# Create a new Flask web server instance
app = Flask(__name__)

# Load environment variables from a .env file
load_dotenv(find_dotenv())

# Get the MongoDB host URI from environment variables
mongo_host = os.environ.get("MONGO_HOST_prim")

def get_timesheets_for_employee(client, employee_id):
    """
    Retrieves all timesheets for an employee from the database.

    Args:
        client (MongoClient): An instance of MongoClient.
        employee_id (str): The ID of the employee.

    Returns:
        JSON response: A JSON response containing the timesheets or an error message.
    """
    try: 
        # Access the 'EmployeeSheets' collection
        employee_sheets_collection = client.TimesheetDB.EmployeeSheets
        members_collection = client.WorkBaseDB.Members
        members_collection = client.WorkBaseDB.Members

        # Use aggregation pipeline to match the employee ID and project the required fields
        pipeline = [    {"$match": {"employeeID": ObjectId(employee_id)}},
                        {"$lookup": {"from": "ManagerSheets",
                                    "localField": "managerSheetID",
                                    "foreignField": "_id",
                                    "as": "managerSheet"}},
                        {"$lookup": {"from": "TimesheetRecords",
                                    "localField": "managerSheet._id",
                                    "foreignField": "ManagerSheetInstances.ManagerSheetObjects",
                                    "as": "manager"}},
                        {"$project": {"ManagerID": "$manager.managerID",
                                      "StartDate": "$manager.startDate",
                                      "StartDate": "$manager.endDate",
                                    "EmployeeSheetVersion":
                                    "$employeeSheetInstances.version",
                                    "EmployeeSheetStatus": "$status",
                                    "WorkDayDetails": "$employeeSheetInstances.employeeSheetObject.workDay",
                                    "Description":    "$employeeSheetInstances.employeeSheetObject.description"}}
                    ]

        # pipeline = [
        #     {"$match": {"employeeID": ObjectId(employee_id)}},
        #     {"$unwind": "$employeeSheetInstances"},
        #     {"$lookup": {
        #         "from": "ManagerSheets",
        #         "localField": "managerSheetID",
        #         "foreignField": "_id",
        #         "as": "managerSheet"
        #     }}, 

        # Aggregate the employee_sheets collection using the pipeline
        employee_sheets = employee_sheets_collection.aggregate(pipeline)
        # Convert the employee_sheets cursor object to a list
        timesheets = list(employee_sheets)

        # Check if Timesheet list is empty
        if not timesheets:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # Convert the employee_sheets cursor object to a JSON object
        timesheets_json = json.dumps(timesheets, default=str)
        
        # Return the JSON response
        return make_response(timesheets_json, 200)
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

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
        
        # If the account ID exists, return the corresponding _id
        return make_response(jsonify({"_id": str(account_exists["_id"])}), 200)

    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def get_WorkAccount(client, uid):
    """
    This function retrieves the account details of a user from the database.
    It takes a MongoClient instance and a user ID as input.
    It returns the account details if the user ID exists, or an error response if it does not exist or if an error occurs.
    """
    try:
        # print(uid)
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

def fetch_timesheets(employee_uuid):
    """
    This function fetches all timesheets (or draft timesheets) for an employee.
    It takes an employee ID as input.
    It returns a JSON response containing the timesheets or an error message.
    """
    try: 
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        if isinstance(client, MongoClient):
            # check if the userID is valid
            verify = get_WorkAccount(client,employee_uuid)
            if not verify.status_code == 200:
                # If the connection fails, return the error response
                return verify
            
            # return make_response(jsonify({"message": "working"}), 200)

            employee_id = verify.json["_id"]
            # Call the get_timesheets_for_employee function with the employee ID
            timesheets_response = get_timesheets_for_employee(client, employee_id)  
            
            return timesheets_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

