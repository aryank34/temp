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
        # Use aggregation pipeline to match the employee ID and project the required fields
        timesheet_pipeline = [ 
                                {"$match": {"employeeID": ObjectId(employee_id)}},
                                {"$project": {"Manager":  "$managerID",
                                                "StartDate":  "$startDate",
                                                "EndDate":    "$endDate",
                                                "employeeSheetInstances":   "$employeeSheetInstances",
                                                "Status":  "$status"}}
                            ]
        timesheets = list(client.TimesheetDB.EmployeeSheets.aggregate(timesheet_pipeline))

        # Check if Timesheet list is empty
        if not timesheets:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)
        
        work_pipeline = [
                            {"$unwind": "$assignedTo",},
                            {"$lookup": {"from": "Members",
                                        "localField": "assignedTo",
                                        "foreignField": "_id",
                                        "as": "member"}},
                            {"$unwind": "$member"},
                            {"$lookup": {"from": "Members",
                                        "localField": "assignedBy",
                                        "foreignField": "_id",
                                        "as": "manager"}},
                            {"$unwind": "$manager"},
                            {"$lookup": {"from": "Tasks",
                                        "localField": "taskID",
                                        "foreignField": "_id",
                                        "as": "task"}},
                            {"$unwind": "$task"},
                            {"$lookup": {"from": "Projects",
                                        "localField": "task.projectID",
                                        "foreignField": "_id",
                                        "as": "project"}},
                            {"$unwind": "$project"},
                            {"$project": {"Assignment Name": "$name",
                                            "Project": {"projectID": "$project._id",
                                                        "Project Name": "$project.name"},
                                            "Task": {"taskID": "$task._id",
                                                    "Task Name": "$task.name",
                                                    "Billable": "$task.billable",
                                                    "Task Description": "$task.description"},
                                            "Employee": {"employeeID": "$member._id",
                                                        "Employee Name": "$member.name"},
                                            "Manager": {"managerID": "$manager._id",
                                                        "Manager Name": "$manager.name"}}},
                            {"$match": {"Employee.employeeID": ObjectId(employee_id)}}
                        ]

        work = list(client.WorkBaseDB.Assignments.aggregate(work_pipeline))

        manager_dict, project_dict, task_dict = ({item[key]['managerID' if key == 'Manager' else 'projectID' if key == 'Project' else 'taskID']: item[key] for item in work} for key in ['Manager', 'Project', 'Task'])
        for i in range(len(timesheets)):
            manager_id = timesheets[i]['Manager']
            manager_item = manager_dict.get(manager_id)
            if manager_item:
                # Merge Manager details
                timesheets[i]['Manager'] = manager_item

                # Merge Project and Task details in employeeSheetInstances
                for j in range(len(timesheets[i]['employeeSheetInstances'])):
                    project_id = timesheets[i]['employeeSheetInstances'][j]['employeeSheetObject'].pop('projectID', None)
                    if project_id is not None:
                        project_item = project_dict.get(project_id)
                        if project_item:
                            timesheets[i]['employeeSheetInstances'][j]['employeeSheetObject']['Project'] = project_item
                    task_id = timesheets[i]['employeeSheetInstances'][j]['employeeSheetObject'].pop('taskID', None)
                    if task_id is not None:
                        task_item = task_dict.get(task_id)
                        if task_item:
                            timesheets[i]['employeeSheetInstances'][j]['employeeSheetObject']['Task'] = task_item


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

