import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import find_dotenv, load_dotenv
from flask import jsonify, make_response
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime

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

def distribute_timesheets():
    # Create a connection to the MongoDB database
    client = dbConnectCheck()
    
    # Select the databases
    timesheet_db = client.TimesheetDB
    workbase_db = client.WorkBaseDB

    # Get the collections
    manager_sheets_collection = timesheet_db.ManagerSheets
    assignments_collection = workbase_db.Assignments
    members_collection = workbase_db.Members
    employee_sheets_collection = timesheet_db.EmployeeSheets

    # Get the current date
    current_date = datetime.datetime.now()

    # Find the manager sheets for the current week
    manager_sheets = manager_sheets_collection.find({"startDate": {"$lte": current_date}, "endDate": {"$gte": current_date}})

    for manager_sheet in manager_sheets:
        # Get the assignment details
        assignment = assignments_collection.find_one({"_id": manager_sheet["assignmentId"]})
        
        

        # Get the employee details
        member = members_collection.find_one({"_id": assignment["assignedTo"]})

        # Distribute a copy of the manager sheet to the employee
        employee_sheet = manager_sheet.copy()
        employee_sheet["employeeId"] = member["_id"]
        employee_sheets_collection.insert_one(employee_sheet)

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(distribute_timesheets, 'cron', day_of_week='sun', hour=0, minute=0)
scheduler.start()