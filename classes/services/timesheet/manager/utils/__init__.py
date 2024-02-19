# Import necessary modules
from datetime import datetime, timedelta
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
from ....connectors.dbConnector import dbConnectCheck, get_WorkAccount, verify_attribute

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
                            {"$match": {"managerID": ObjectId(manager_id)}},
                            {"$unwind": "$managerSheetsInstances"},
                            {"$lookup": {
                                "from": "ManagerSheets",
                                "localField": "managerSheetsInstances.managerSheetsObjects",
                                "foreignField": "_id",
                                "as": "managerSheets"}},
                            {"$unwind": "$managerSheets"},
                            {"$project": {"managerSheetID": "$managerSheets._id",
                                        "Last Update Date": "$managerSheetsInstances.lastUpdateDate",
                                        "Sheet Version": "$managerSheetsInstances.version",
                                        "Project": "$managerSheets.projectID",
                                        "Start Date": "$managerSheets.startDate",
                                        "End Date": "$managerSheets.endDate",
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
                    {"$match": {"managerID": ObjectId(manager_id)}},
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
        


        # Check the status of the timesheets
        if status == "Draft" or status == "Assign":
            timesheet = timesheet_collection.aggregate(default_pipeline)
        elif status is "Review":
            # return make_response(jsonify({"message": "Working in review"}), 200)
            timesheet = timesheet_collection.aggregate(review_pipeline)

        # Check if Timesheet Exists
        if not timesheet:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)
        
        filtered_timesheets = []
        if status == "Draft":
            query = ["Draft"]
        # is statuses of timesheet is manage, select Active, Upcoming, and review
        elif status == "Assign":
            query = ["Active", "Upcoming"]
        elif status == "Review":
            query = ["Review"]

        for ts in timesheet:
            if ts.get('Status') in query:
                filtered_timesheets.append(ts)
            

        # Check if Timesheet list is empty
        if not filtered_timesheets:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # Convert the manager_sheets cursor object to a JSON object
        timesheets_json = json.dumps(filtered_timesheets, default=str)
        # Parse the JSON string into a Python data structure
        timesheets_data = json.loads(timesheets_json)

        # Return the JSON response as managerSheets, preserve the output format
        return make_response(jsonify({"managerSheets": timesheets_data}), 200)

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
    try: 
        # Convert string to ObjectId
        projectID = ObjectId(data["projectID"])
        assignGroupID = ObjectId(data["assignGroupID"])
        # Convert string to datetime
        startDate = datetime.strptime(data['startDate'], "%Y-%m-%d %H:%M:%S")
        endDate = datetime.strptime(data['endDate'], "%Y-%m-%d %H:%M:%S")

        # Extract other fields
        action = data["action"]
        # if action is not "Draft" or "Save", throw error with message: "Illegal Action for timesheet"
        if action not in ["Draft", "Save"]:
            return make_response(jsonify({"error": "Illegal Action for timesheet"}), 400)
        status=""
        if action == "Draft":
            status = "Draft"
        elif action == "Save":
            currentDate = datetime.now()
            if (startDate-currentDate<=timedelta(1)):
                status = "Active"
            else:
                status = "Upcoming"
        
        description = data["description"]

        # Create WorkDay object
        workDay = {
            "mon": WorkDay(data["workDay"]["mon"]),
            "tue": WorkDay(data["workDay"]["tue"]),
            "wed": WorkDay(data["workDay"]["wed"]),
            "thu": WorkDay(data["workDay"]["thu"]),
            "fri": WorkDay(data["workDay"]["fri"]),
            "sat": WorkDay(data["workDay"]["sat"]),
            "sun": WorkDay(data["workDay"]["sun"]),
        }

        # Create ManagerSheetsAssign object
        manager_sheets_assign = ManagerSheetsAssign(projectID = projectID, startDate = startDate, endDate = endDate, workDay = workDay, description = description, status = status, assignGroupID = assignGroupID)
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

        return make_response(jsonify({"message": "Timesheet Creation Successful"}), 200)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

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
                    curr = datetime.now()
                    if (start >= end) or (start<=curr) or (end<=curr):
                        return make_response(jsonify({"error": "timesheet duration data is incorrect"}), 400)
                else:
                    return make_response(jsonify({"error": "timesheet duration data is required"}), 400)

            else:
                return make_response(jsonify({"error": "timesheet data is required"}), 400)


            
            newmanagerSheet=store_data(timesheet,manager_id,client)
            
            if not newmanagerSheet.status_code == 200:
                # If the connection fails, return the error response
                return newmanagerSheet
            # Return the new timesheet as a JSON response
            return make_response(jsonify({"message": str(newmanagerSheet.json['message'])}), 200)    

        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)
