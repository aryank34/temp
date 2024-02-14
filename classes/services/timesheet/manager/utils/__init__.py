# Import necessary modules
from datetime import datetime
from bson import ObjectId
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

        # Use find_one to get the first timesheet that matches the manager ID
        timesheet = timesheet_collection.find_one({"managerID": ObjectId(manager_id)})
        
        # Check if Timesheet Exists
        if not timesheet:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # Access the 'ManagerSheets' collection
        manager_sheets_collection = client.TimesheetDB.ManagerSheets
        timesheetIDs = [instance['managerSheetsObjects'] for instance in timesheet['managerSheetsInstances']]

        # Check if Timesheet Exists
        if len(timesheetIDs) == 0:
            # Resturn No Timesheets Response if list empty
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # Find the list of managerSheets with equivalent timesheetIDs
        query = {"_id": {"$in": timesheetIDs}}

        # is statuses of timesheet is draft
        if status is "Draft":
            query["status"] = status
        # is statuses of timesheet is manage, select Active, Upcoming, and review
        if status is "Manage":
            query["status"] = {"$in": ["Active", "Upcoming", "Review"]}
        manager_sheets = manager_sheets_collection.find(query)
        
        # Convert the manager_sheets cursor object to a list
        timesheets = list(manager_sheets)

        # Check if Timesheet list is empty
        if not timesheets:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # Convert the manager_sheets cursor object to a JSON object
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
        client = MongoClient(uri, server_api=ServerApi('1'))

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

def fetch_timesheets(manager_id, status=None):
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
            verify = verify_attribute(collection=client.WorkBaseDB.Members,key="_id", attr_value=ObjectId(manager_id))
            if not verify.status_code == 200:
                # If the connection fails, return the error respons
                return verify
            
            # Call the get_timesheets_for_manager function with the manager ID
            timesheets_response = get_timesheets_for_manager(client, manager_id, status)  
            
            return timesheets_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def create_timesheet(manager_id, timesheet):
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
            verify = verify_attribute(collection=client.WorkBaseDB.Members, key="_id", attr_value=ObjectId(manager_id))
            if not verify.status_code == 200:
                # If the connection fails, return the error response
                return verify
            

            if timesheet is not None:

                # check if assignGroupID is valid
                if timesheet['assignGroupID'] is not None:
                    timesheet['assignGroupID'] = ObjectId(timesheet['assignGroupID'])
                    verify = verify_attribute(collection=client.TimesheetDB.AssignmentGroup, key="_id",attr_value=timesheet['assignGroupID'])
                    if not verify.status_code == 200:
                        # If the connection fails, return the error response
                        return verify
                    
                if 'projectID' in timesheet:
                    timesheet['projectID'] = ObjectId(timesheet['projectID'])
                    # check if projectID is valid
                    verify = verify_attribute(collection=client.WorkBaseDB.Projects, key="_id",attr_value=timesheet['projectID'])
                    if not verify.status_code == 200:
                        # If the connection fails, return the error response
                        return verify
                    
                if 'startDate' in timesheet:
                    timesheet['startDate'] = datetime.strptime(timesheet['startDate'], "%Y-%m-%d %H:%M:%S")
                if 'endDate' in timesheet:
                    timesheet['endDate'] = datetime.strptime(timesheet['endDate'], "%Y-%m-%d %H:%M:%S")

                # check if startDate is greater than endDate format:2024-02-05 18:30:00
                if timesheet['startDate'] > timesheet['endDate']:
                    return make_response(jsonify({"error": "startDate cannot be greater than endDate"}), 400)

            else:
                return make_response(jsonify({"error": "timesheet data is required"}), 400)


            
            # Access the 'TimesheetRecords' collection
            timesheet_collection = client.TimesheetDB.TimesheetRecords

            # Access the 'ManagerSheets' collection
            manager_sheets_collection = client.TimesheetDB.ManagerSheets

            # Create a new timesheet object in managerSheets Collection and fetch the new timesheet ID
            new_timesheet = manager_sheets_collection.insert_one(timesheet)
            new_timesheet_id = new_timesheet.inserted_id

            managersheetobject = {
                "createdDate": datetime.now(),
                "managerSheetsObjects": new_timesheet_id}

            # Update the managerSheetsObjects field in TimesheetRecords Collection, if managerID is not matched create new entry
            if (timesheet_collection.find_one({"managerID": ObjectId(manager_id)})) is None:
                timesheet_collection.insert_one(
                    {"managerID": ObjectId(manager_id), "managerSheetsInstances": [managersheetobject]}
                )
            else:
                timesheet_collection.update_one(
                {"managerID": ObjectId(manager_id)},
                {"$push": {"managerSheetsInstances": managersheetobject}}
            )

            # Return the new timesheet as a JSON response
            return make_response(jsonify({"message": "Timesheet created successfully", "timesheetID": str(new_timesheet.inserted_id)}), 200)

        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)
