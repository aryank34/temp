# Import necessary libraries and modules
from apscheduler.schedulers.background import BackgroundScheduler
from bson import ObjectId
from pymongo import MongoClient
import pandas as pd

# Import necessary models and connectors
from ...workbase import models
from ..models import EmployeeSheet, EmployeeSheetInstance, EmployeeSheetObject, WorkDay 
from ...connectors.dbConnector import dbConnectCheck

# Import utility functions
from .utils import get_next_week

# Function to update the status of upcoming timesheets to active
def upcoming_to_active_timesheets(client):
    # run only every Sunday
    
    # Get the collections
    manager_sheets_collection = client.TimesheetDB.ManagerSheets

    # Get next week
    next_monday, next_to_next_monday = get_next_week()

    # Find all documents where the startDate is in the next week
    documents = list(manager_sheets_collection.find({"startDate": {"$gte": next_monday, "$lt": next_to_next_monday},"status": "Upcoming"}, {"_id": 1}))

    # in ManagerSheets, update all these documents status to active
    for document in documents:
        manager_sheets_collection.update_one({"_id": document["_id"]}, {"$set": {"status": "Active"}})

# Function to store employee sheets in the database
def store_employee_sheets(data,client):
    try: 
        # Create WorkDay object
        workDay = {
            "mon": WorkDay(data["workDay"]["mon"]["work"]),
            "tue": WorkDay(data["workDay"]["tue"]["work"]),
            "wed": WorkDay(data["workDay"]["wed"]["work"]),
            "thu": WorkDay(data["workDay"]["thu"]["work"]),
            "fri": WorkDay(data["workDay"]["fri"]["work"]),
            "sat": WorkDay(data["workDay"]["sat"]["work"]),
            "sun": WorkDay(data["workDay"]["sun"]["work"]),
        }

        # EmployeeSheetObjectModel data
        projectID = ObjectId(data["Project"]["projectID"])
        taskID = ObjectId(data["Task"]["taskID"])
        description = data["description"]

        employeeSheetObject = EmployeeSheetObject(projectID=projectID, taskID=taskID, workDay=workDay, description=description)
        
        # EmployeeSheetInstanceModel data
        version = data["version"]

        employeeSheetInstance = EmployeeSheetInstance(version=version, employeeSheetObject=employeeSheetObject) 

        # EmployeeSheetModel data
        managerSheetID = ObjectId(data["managerSheetID"])
        employeeID = ObjectId(data["Employee"]["employeeID"])
        managerID = ObjectId(data["Manager"]["managerID"])
        startDate = data["startDate"]
        endDate = data["endDate"]

        employeeSheet = EmployeeSheet(managerSheetID=managerSheetID, employeeID=employeeID, managerID=managerID, startDate=startDate, endDate=endDate, employeeSheetInstances=[employeeSheetInstance])

        # Update the EmployeeSheets Collection, if employeeSheets is not matched create new entry
        if (client.TimesheetDB.EmployeeSheets.find_one({"managerSheetID": employeeSheet.managerSheetID,
                                                        "employeeID": employeeSheet.employeeID}) is None):
            result = client.TimesheetDB.EmployeeSheets.insert_one(employeeSheet.to_dict())
            msg_str = "Employee Sheet Created"
        else:
            if (client.TimesheetDB.EmployeeSheets.find_one({"employeeSheetInstances.version": version}) is None):
                result = client.TimesheetDB.EmployeeSheets.update_one({"employeeID": employeeSheet.employeeID, "managerSheetID": employeeSheet.managerSheetID},
                                                            {"$push": {"employeeSheetInstances": employeeSheetInstance.to_dict()}})
                msg_str = "Employee Sheet updated"
            
        print(msg_str,": EmployeeSheetID :", result.inserted_id)


    except Exception as e:
        # If an error occurs, return the error response
        print("Error creating Timesheet Records: ", e)
        
# Function to distribute active timesheets
def distribute_active_timesheets(client):
    managerSheet_pipeline = [
                            {"$unwind": "$managerSheetsInstances"},
                            {"$lookup":{"from": "ManagerSheets",
                                        "localField": "managerSheetsInstances.managerSheetsObjects",
                                        "foreignField": "_id",
                                        "as": "manager"}},
                            {"$unwind": "$manager"},
                            {"$match":{ "manager.status": "Active"}},
                            {"$lookup":{"from": "AssignmentGroup",
                                        "localField": "manager.assignGroupID",
                                        "foreignField": "_id",
                                        "as": "assign"}},
                            {"$unwind": "$assign"},
                            {"$project":{"managerID": 1,
                                        "version": "$managerSheetsInstances.version",
                                        "managerSheetID": "$managerSheetsInstances.managerSheetsObjects",
                                        "startDate": "$manager.startDate",
                                        "endDate": "$manager.endDate",
                                        "status": "$manager.status",
                                        "projectID": "$manager.projectID",
                                        "workDay": "$manager.workDay",
                                        "description": "$manager.description",
                                        "assignmentID": "$assign.assignmentInstances.assignmentID"}},
                            {"$unwind": "$assignmentID"}
                        ]

    assignment_pipeline =   [
                            {"$unwind": "$assignedTo"},
                            {"$lookup":{"from": "Members",
                                        "localField": "assignedTo",
                                        "foreignField": "_id",
                                        "as": "member"}},
                            {"$unwind": "$member"},
                            {"$lookup":{"from": "Members",
                                        "localField": "assignedBy",
                                        "foreignField": "_id",
                                        "as": "manager"}},
                            {"$unwind": "$manager"},
                            {"$lookup":{"from": "Tasks",
                                        "localField": "taskID",
                                        "foreignField": "_id",
                                        "as": "task"}},
                            {"$unwind": "$task"},
                            {"$lookup":{"from": "Projects",
                                        "localField": "task.projectID",
                                        "foreignField": "_id",
                                        "as": "project"}},
                            {"$unwind": "$project"},
                            {"$project":{"_id":0,
                                        "assignmentID": "$_id",
                                        "Assignment Name": "$name",
                                        "Project":{"projectID": "$project._id",
                                                    "Project Name": "$project.name"},
                                        "Task":{   "taskID": "$task._id",
                                                    "Task Name": "$task.name",
                                                    "Billable": "$task.billable",
                                                    "Task Description": "$task.description",},
                                        "Employee":{"employeeID": "$member._id",
                                                    "Employee Name": "$member.name"},
                                        "Manager":{"managerID": "$manager._id",
                                                    "Manager Name": "$manager.name"}}}
                        ]

    timesheet_documents = list(client.TimesheetDB.TimesheetRecords.aggregate(managerSheet_pipeline))
    assignment_documents = list(client.WorkBaseDB.Assignments.aggregate(assignment_pipeline))
    
    # Convert MongoDB query results to DataFrames
    timesheet_df = pd.DataFrame(timesheet_documents)
    assignment_df = pd.DataFrame(assignment_documents)
    result_df = pd.merge(timesheet_df, assignment_df, on='assignmentID', how='inner')
    result_documents = result_df.to_dict(orient='records')
    for i in range(len(result_documents)):
        subset_dict = {key: result_documents[i][key] for key in ['managerSheetID', 'startDate', 'endDate', 'status', 'version', 'workDay', 'description', 'Project', 'Task', 'Employee', 'Manager'] if key in result_documents[i]}
        # doc_res.append(subset_dict)
        store_employee_sheets(subset_dict, client)

def main():
    # Connect to the database   
    client = dbConnectCheck()

    # Check if the client is a MongoClient instance
    if isinstance(client, MongoClient):
        # Initialize the scheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(upcoming_to_active_timesheets, 'cron', day_of_week='sun', hour=0, minute=0, timezone='America/New_York', args=[client])
        scheduler.add_job(distribute_active_timesheets, 'cron', day_of_week='*', hour=15, minute=0, timezone='Asia/Kolkata', args=[client])
        scheduler.start()
    else:
        # If the connection fails, return the error response
        print("Failed to connect to the MongoDB server")

if __name__ == "__main__":
    main()