# Import necessary modules
from datetime import datetime
from uuid import UUID
from bson import ObjectId
from bson.binary import UuidRepresentation
from flask import Flask, jsonify, make_response
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv, find_dotenv
import json
from ...models import TimesheetRecord,ManagerSheetsAssign,ManagerSheetsInstance,WorkDay

# Create a new Flask web server instance
app = Flask(__name__)

# Load environment variables from a .env file
load_dotenv(find_dotenv())

# Get the MongoDB host URI from environment variables
mongo_host = os.environ.get("MONGO_HOST_prim")

def get_timesheets_for_manager(client, manager_id, status=None):
    """
    Retrieves all timesheets (or draft timesheets) for a manager from the database.

    Args:
        client (MongoClient): An instance of MongoClient.
        manager_id (str): The ID of the manager.
        status (str, optional): The status of the timesheets to retrieve. If None, retrieves all timesheets.

    Returns:
        JSON response: A JSON response containing the timesheets or an error message.
    """
    try: 
        # Access the 'TimesheetRecords' collection
        timesheet_collection = client.TimesheetDB.TimesheetRecords

        

        # Use aggregation pipeline to match the employee ID and project the required fields
        default_pipeline = [
                            {"$match": {"managerID": ObjectId("65c408582b6c3e4c3208296d")}},
                            {"$unwind": "$managerSheetsInstances"},
                            {"$lookup": {
                                "from": "ManagerSheets",
                                "localField": "managerSheetsInstances.managerSheetsObjects",
                                "foreignField": "_id",
                                "as": "managerSheets"}},
                            {"$unwind": "$managerSheets"},
                            {"$project": {"createdDate": "$managerSheetsInstances.createdDate",
                                        "Project": "$managerSheets.projectID",
                                        "startDate": "$managerSheets.startDate",
                                        "endDate": "$managerSheets.endDate",
                                        "Status": "$managerSheets.status",
                                        "WorkDay": {
                                            "$arrayToObject": {
                                            "$map": {
                                                "input": {"$objectToArray": "$managerSheets.workDay"},
                                                "as": "day",
                                                "in": {
                                                "k": "$$day.k",
                                                "v": "$$day.v.work"}}}},
                                        "Description": "$managerSheets.description",
                                        "Assigned To": "$managerSheets.assignGroupID"
                                        }}
                            ]
        review_pipeline = [
                    {"$match": {"managerID": ObjectId("65c408582b6c3e4c3208296d")}},
                    {"$unwind": "$managerSheetsInstances"},
                    {"$lookup": {
                        "from": "ManagerSheets",
                        "localField": "managerSheetsInstances.managerSheetsObjects",
                        "foreignField": "_id",
                        "as": "managerSheets"}},
                    {"$match": {
                        "managerSheets.status": "Review"
                    }},
                    {"$unwind": "$managerSheets"},
                    {"$project": {"Employee": "$managerSheets.employeeID",
                                "Project": "$managerSheets.employeeSheetInstances.employeeSheetObject.projectID",
                                "Task": "$managerSheets.employeeSheetInstances.employeeSheetObject.taskID",
                                "startDate": "$managerSheets.startDate",
                                "endDate": "$managerSheets.endDate",
                                "Status": "$managerSheets.status",
                                "WorkDay": "$managerSheets.employeeSheetInstances.employeeSheetObject.workDay",
                                "Description": "$managerSheets.employeeSheetInstances.employeeSheetObject.description"
                                }}
                    ]
        # return working response

        if status is "Draft" or status is "Assign":
            timesheet = timesheet_collection.aggregate(default_pipeline)
        elif status is "Review":
            # return make_response(jsonify({"message": "Working in review"}), 200)
            timesheet = timesheet_collection.aggregate(review_pipeline)

        # Check if Timesheet Exists
        if not timesheet:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)
        
        filtered_timesheets = []
        if status is "Draft":
            query = ["Draft"]
        # is statuses of timesheet is manage, select Active, Upcoming, and review
        elif status is "Assign":
            query = ["Active", "Upcoming"]
        elif status is "Review":
            query = ["Review"]

        for ts in timesheet:
            if ts.get('Status') in query:
                filtered_timesheets.append(ts)
            

        # Check if Timesheet list is empty
        if not filtered_timesheets:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # Convert the manager_sheets cursor object to a JSON object
        timesheets_json = json.dumps(filtered_timesheets, default=str)
        
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
        return make_response(jsonify({"message": "Account ID exists"}), 200)

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

def fetch_timesheets(manager_uuid, status=None):
    """
    This function fetches all timesheets (or draft timesheets) for a manager.
    It takes a manager ID as input.
    It returns a JSON response containing the timesheets or an error message.
    """
    try: 
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        if isinstance(client, MongoClient):
            # check if the userID is valid
            verify = get_WorkAccount(client, manager_uuid)
            if not verify.status_code == 200:
                # If the connection fails, return the error respons
                return verify
            
            manager_id = verify.json['_id']
            # Call the get_timesheets_for_manager function with the manager ID
            timesheets_response = get_timesheets_for_manager(client, manager_id, status)  
            
            return timesheets_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def store_data(data,manager_id,client):
    # Convert string to ObjectId
    projectID = ObjectId(data["projectID"])
    assignGroupID = ObjectId(data["assignGroupID"])
    # Convert string to datetime
    startDate = datetime.strptime(data['startDate'], "%Y-%m-%d %H:%M:%S")
    endDate = datetime.strptime(data['endDate'], "%Y-%m-%d %H:%M:%S")

    # Extract other fields
    status = data["status"]
    description = data["description"]

    # Create WorkDay object
    workDay = {
        "mon": WorkDay(data["workDay"]["mon"], 0, ""),
        "tue": WorkDay(data["workDay"]["tue"], 0, ""),
        "wed": WorkDay(data["workDay"]["wed"], 0, ""),
        "thu": WorkDay(data["workDay"]["thu"], 0, ""),
        "fri": WorkDay(data["workDay"]["fri"], 0, ""),
        "sat": WorkDay(data["workDay"]["sat"], 0, ""),
        "sun": WorkDay(data["workDay"]["sun"], 0, ""),
    }

    # Create ManagerSheetsAssign object
    manager_sheets_assign = ManagerSheetsAssign(projectID = projectID, startDate = startDate, endDate = endDate, workDay = workDay, description = description, status = status, assignGroupID = assignGroupID, sheetUpdate = False)
    # Create a new timesheet object in managerSheets Collection and fetch the new timesheet ID
    new_timesheet = client.TimesheetDB.ManagerSheets.insert_one(manager_sheets_assign.to_dict())
    new_timesheet_id = new_timesheet.inserted_id
    # Create ManagerSheetsInstance object
    lastUpdateDate = datetime.now()
    manager_sheets_instance = ManagerSheetsInstance(lastUpdateDate=lastUpdateDate, managerSheetsObjectID=new_timesheet_id)

    # Update the managerSheetsObjects field in TimesheetRecords Collection, if managerID is not matched create new entry
    if (client.TimesheetDB.TimesheetRecords.find_one({"managerID": ObjectId(manager_id)})) is None:
        client.TimesheetDB.TimesheetRecords.insert_one({"managerID": ObjectId(manager_id), 
                                                        "managerSheetsInstances": [manager_sheets_instance.to_dict()]})
    else:
        client.TimesheetDB.TimesheetRecords.update_one({"managerID": ObjectId(manager_id)},
                                                       {"$push": {"managerSheetsInstances": manager_sheets_instance.to_dict()}}
    )

    return new_timesheet_id

def create_timesheet(manager_uuid, timesheet):
    """
    This function creates a new timesheet for a manager.
    It takes the manager ID, timesheet data, and the collection to save to as input.
    It returns a JSON response containing the new timesheet or an error message.
    """
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()

        if isinstance(client, MongoClient):

            # correct data field formats for timesheet
            # check if the managerID is valid
            verify = get_WorkAccount(client, manager_uuid)
            if not verify.status_code == 200:
                # If the connection fails, return the error response
                return verify
            manager_id= verify.json['_id']


            if timesheet is not None:

                # check if assignGroupID is valid
                if timesheet['assignGroupID'] is not None:
                    timesheet['assignGroupID'] = ObjectId(timesheet['assignGroupID'])
                    verify = verify_attribute(collection=client.TimesheetDB.AssignmentGroup, key="_id",attr_value=timesheet['assignGroupID'])
                    if not verify.status_code == 200:
                        # If the connection fails, return the error response
                        return verify
                else:
                    return make_response(jsonify({"error": "timesheet \"assignGroupID\" data is required"}), 400)

                # check if projectID is valid
                if 'projectID' in timesheet:
                    timesheet['projectID'] = ObjectId(timesheet['projectID'])
                    verify = verify_attribute(collection=client.WorkBaseDB.Projects, key="_id",attr_value=timesheet['projectID'])
                    if not verify.status_code == 200:
                        # If the connection fails, return the error response
                        return verify
                else:
                    return make_response(jsonify({"error": "timesheet \"projectID\" data is required"}), 400)
                    
                # check if startDate is greater than endDate format:2024-02-05 18:30:00
                if 'startDate' in timesheet and 'endDate' in timesheet:
                    start = datetime.strptime(timesheet['startDate'], "%Y-%m-%d %H:%M:%S")
                    end = datetime.strptime(timesheet['endDate'], "%Y-%m-%d %H:%M:%S")
                    if start >= end:
                        return make_response(jsonify({"error": "startDate cannot be greater than endDate"}), 400)
                else:
                    return make_response(jsonify({"error": "timesheet duration data is required"}), 400)

            else:
                return make_response(jsonify({"error": "timesheet data is required"}), 400)


            
            newmanagerSheet=store_data(timesheet,manager_id,client)

            # Return the new timesheet as a JSON response
            return make_response(jsonify({"message": "Timesheet created successfully", "timesheetID": str(newmanagerSheet)}), 200)

        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)
