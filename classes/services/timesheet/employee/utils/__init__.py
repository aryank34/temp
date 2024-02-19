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

from ....connectors.dbConnector import dbConnectCheck, get_WorkAccount

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

        # Use aggregation pipeline to match the employee ID and project the required fields
        pipeline = [ 
        #             {"$match": 
        #             {"employeeID": ObjectId(employee_id)}},
        #             {"$project": {"Manager":  "$managerID",
        #                           "StartDate":  "$startDate",
        #                           "EndDate":    "$endDate",
        #                         #   "EmployeeSheetVersion":   "$employeeSheetInstances.version",
        #                           "Status":  "$status",
        #                           "Project":   "$employeeSheetInstances.employeeSheetObject.projectID",
        #                           "Task":  "$employeeSheetInstances.employeeSheetObject.taskID",
        #                           "WorkDayDetails":   "$employeeSheetInstances.employeeSheetObject.workDay",
        #                           "Description":  "$employeeSheetInstances.employeeSheetObject.description"
        #             }}
        #             ]    
                        {"$match": 
                        {"employeeID": ObjectId(employee_id)}},
                        {"$project": {"Manager":  "$managerID",
                            "StartDate":  "$startDate",
                            "EndDate":    "$endDate",
                        "employeeSheetInstances":   "$employeeSheetInstances",
                            "Status":  "$status"
                        }}
                    ]
        

        # Aggregate the employee_sheets collection using the pipeline
        employee_sheets = employee_sheets_collection.aggregate(pipeline)
        # Convert the employee_sheets cursor object to a list
        timesheets = list(employee_sheets)

        # Check if Timesheet list is empty
        if not timesheets:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # Convert the employee_sheets cursor object to a JSON object
        timesheets_json = json.dumps(timesheets, default=str)
        timesheets_data = json.loads(timesheets_json)
        # Return the JSON response
        return make_response(jsonify({"employeeSheets": timesheets_data}), 200)
    
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

