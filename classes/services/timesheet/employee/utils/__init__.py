# Import necessary modules
from datetime import datetime, timedelta
from bson import ObjectId
from flask import jsonify, make_response
from pymongo import MongoClient
import json
from ...models import EmployeeSheetObject, EmployeeSheet, ManagerSheetReview, WorkDay
from ....connectors.dbConnector import dbConnectCheck, get_WorkAccount, verify_attribute

def get_submitted_timesheets_for_employee(client, employee_id):
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
        timesheet_pipeline = [  {"$match": {"employeeID": ObjectId(employee_id)}},
                                {"$match": {"status": {"$in": ["Reviewing","Submitted"]}}},
                                {"$group": {"_id": {"employeeID": "$employeeID","status": "$status"},
                                          "sheets": {"$push": {"employeeSheetID": "$_id","startDate": "$startDate","endDate": "$endDate","employeeSheetObjects": "$employeeSheetObject","Status": "$status","ReturnedMessage": "$returnMessage"}}}},
                                {"$group": {"_id": "$_id.employeeID","employeeSheet": {"$push": {"k": "$_id.status","v": "$sheets"}}}},
                                {"$replaceRoot": {"newRoot": {"$mergeObjects": [{ "$arrayToObject": "$employeeSheet" },{ "_id": "$_id" }]}}},
                                {"$project": {"_id": 0,"Reviewing": 1,"Submitted": 1}}
                        ]
        timesheet_list = list(client.TimesheetDB.EmployeeSheets.aggregate(timesheet_pipeline))

        # return make_response(jsonify({"messages": "OK"}), 200)
        # Check if Timesheet list is empty
        if not timesheet_list:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)
        
        timesheets = timesheet_list[0]
        broadcast_id = client.WorkBaseDB.Members.find_one({"name": "ALL EMPLOYEES"})['_id']
        work_data_pipeline = [  {"$match": {"_id": {"$in": [ObjectId(employee_id),ObjectId(broadcast_id)]}}},
                                {"$lookup": {"from": "ProjectActivity","localField": "_id","foreignField": "activities.members","as": "matchingAssignments"}},
                                {"$unwind": "$matchingAssignments"},
                                {"$lookup": {"from": "Projects","localField": "matchingAssignments.projectID","foreignField": "_id","as": "matchingAssignments.project"}},
                                {"$unwind": "$matchingAssignments.project"},
                                {"$lookup": {"from": "Tasks","localField": "matchingAssignments.activities.tasks","foreignField": "_id","as": "matchingAssignments.task"}},
                                {"$unwind": "$matchingAssignments.task"},
                                {"$group": {"_id": {"employee_id": "$_id","project_id": "$matchingAssignments.project._id"},"project_name": { "$first": "$matchingAssignments.project.name" },"Tasks": { "$push": "$matchingAssignments.task" }}},
                                {"$group": {"_id": "$_id.employee_id","Projects": {"$push": {"_id": "$_id.project_id","name": "$project_name","Tasks": "$Tasks"}}}},
                                {"$project": {"_id": 0,"employeeID": "$_id","Projects": 1}},
                                {"$project": {"Projects.Tasks.projectID": 0,"Projects.Tasks.deadline": 0,"Projects.Tasks.joblist": 0,"Projects.Tasks.completionStatus": 0,}}
                            ]
        # employee_pipeline = [{"$match": {"_id": ObjectId(employee_id)}}]
        # broadcast_pipeline = [{"$match": {"_id": ObjectId(broadcast_id)}}]
        
        # employee_pipeline.extend(common_work_data_pipeline)
        # broadcast_pipeline.extend(common_work_data_pipeline)
        # employee_tasks = list(client.WorkBaseDB.Members.aggregate(employee_pipeline))
        # common_tasks = list(client.WorkBaseDB.Members.aggregate(broadcast_pipeline))
        work_details = list(client.WorkBaseDB.Members.aggregate(work_data_pipeline))
        # if len(employee_tasks) == 0 and len(common_tasks) == 0:
        if len(work_details) == 0:
            return make_response(jsonify({"message": "No Job Assignments Here Yet. Ask the Administrator to Assign you to a Project Activity"}), 400)
        # If the employee has no tasks, return the common tasks
        # if len(employee_tasks) == 0:
        #     employee_tasks = common_tasks
        # # If the employee has tasks, return the employee tasks
        # if len(common_tasks) != 0:
        #     # If the employee has tasks and common tasks, merge the common tasks with the employee tasks
        #     # For each employee task, add the common tasks to the employee tasks
        #     employee_tasks[0]['Projects'].extend(common_tasks[0]['Projects'])
        employee_tasks = work_details[0]['Projects']
        

        # replace projectID with project:{projectName: <ProjectName>, projectId: <ProjectID>} and taskID with task:{taskName: <TaskName>, taskId: <TaskID>} in the timesheet using the employee_tasks dictionary
        if 'Reviewing' in timesheets:
            for i in range(len(timesheets['Reviewing'])):
                for j in range(len(timesheets['Reviewing'][i]['employeeSheetObjects'])):
                    project_id = timesheets['Reviewing'][i]['employeeSheetObjects'][j].pop('projectID', None)
                    if project_id is not None:
                        for project in employee_tasks:
                            if project['_id'] == project_id:
                                timesheets['Reviewing'][i]['employeeSheetObjects'][j]['Project'] = dict({'projectID': project['_id'], 'projectName': project['name']})
                    task_id = timesheets['Reviewing'][i]['employeeSheetObjects'][j].pop('taskID', None)
                    if task_id is not None:
                        for project in employee_tasks:
                            for task in project['Tasks']:
                                if task['_id'] == task_id:
                                    timesheets['Reviewing'][i]['employeeSheetObjects'][j]['Task'] = dict({'taskID': task['_id'], 'taskName': task['name']})
            timesheets['Reviewing'] = sorted(timesheets['Reviewing'], key=lambda x: x['startDate'], reverse=True)
        if 'Submitted' in timesheets:
            for i in range(len(timesheets['Submitted'])):
                for j in range(len(timesheets['Submitted'][i]['employeeSheetObjects'])):
                    project_id = timesheets['Submitted'][i]['employeeSheetObjects'][j].pop('projectID', None)
                    if project_id is not None:
                        for project in employee_tasks:
                            if project['_id'] == project_id:
                                timesheets['Submitted'][i]['employeeSheetObjects'][j]['Project'] = dict({'projectID': project['_id'], 'projectName': project['name']})
                    task_id = timesheets['Submitted'][i]['employeeSheetObjects'][j].pop('taskID', None)
                    if task_id is not None:
                        for project in employee_tasks:
                            for task in project['Tasks']:
                                if task['_id'] == task_id:
                                    timesheets['Submitted'][i]['employeeSheetObjects'][j]['Task'] = dict({'taskID': task['_id'], 'taskName': task['name']})
            timesheets['Submitted'] = sorted(timesheets['Submitted'], key=lambda x: x['startDate'], reverse=True)

        # Convert the employee_sheets cursor object to a JSON object
        timesheets_json = json.dumps(timesheets, default=str)
        timesheets_data = json.loads(timesheets_json)
        # Return the JSON response
        return make_response(jsonify({"employeeSheets": timesheets_data}), 200)
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)


def get_draft_timesheets_for_employee(client, employee_id):
    """
    Retrieves all draft timesheets for an employee from the database.

    Args:
        client (MongoClient): An instance of MongoClient.
        employee_id (str): The ID of the employee.

    Returns:
        JSON response: A JSON response containing the timesheets or an error message.
    """
    try: 
        # Use aggregation pipeline to match the employee ID and project the required fields
        timesheet_pipeline = [  {"$match": {"employeeID": ObjectId(employee_id)}},
                                {"$match": {"status": {"$in": ["Draft"]}}},
                                {"$group": {"_id": {"employeeID": "$employeeID","status": "$status"},
                                          "sheets": {"$push": {"employeeSheetID": "$_id","startDate": "$startDate","endDate": "$endDate","employeeSheetObjects": "$employeeSheetObject","Status": "$status","ReturnedMessage": "$returnMessage"}}}},
                                {"$group": {"_id": "$_id.employeeID","employeeSheet": {"$push": {"k": "$_id.status","v": "$sheets"}}}},
                                {"$replaceRoot": {"newRoot": {"$mergeObjects": [{ "$arrayToObject": "$employeeSheet" },{ "_id": "$_id" }]}}},
                                {"$project": {"_id": 0,"Draft": 1}}
                        ]
        timesheet_list = list(client.TimesheetDB.EmployeeSheets.aggregate(timesheet_pipeline))

        # return make_response(jsonify({"messages": "OK"}), 200)
        # Check if Timesheet list is empty
        if not timesheet_list:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)
        
        timesheets = timesheet_list[0]
        broadcast_id = client.WorkBaseDB.Members.find_one({"name": "ALL EMPLOYEES"})['_id']
        work_data_pipeline = [  {"$match": {"_id": {"$in": [ObjectId(employee_id),ObjectId(broadcast_id)]}}},
                                {"$lookup": {"from": "ProjectActivity","localField": "_id","foreignField": "activities.members","as": "matchingAssignments"}},
                                {"$unwind": "$matchingAssignments"},
                                {"$lookup": {"from": "Projects","localField": "matchingAssignments.projectID","foreignField": "_id","as": "matchingAssignments.project"}},
                                {"$unwind": "$matchingAssignments.project"},
                                {"$lookup": {"from": "Tasks","localField": "matchingAssignments.activities.tasks","foreignField": "_id","as": "matchingAssignments.task"}},
                                {"$unwind": "$matchingAssignments.task"},
                                {"$group": {"_id": {"employee_id": "$_id","project_id": "$matchingAssignments.project._id"},"project_name": { "$first": "$matchingAssignments.project.name" },"Tasks": { "$push": "$matchingAssignments.task" }}},
                                {"$group": {"_id": "$_id.employee_id","Projects": {"$push": {"_id": "$_id.project_id","name": "$project_name","Tasks": "$Tasks"}}}},
                                {"$project": {"_id": 0,"employeeID": "$_id","Projects": 1}},
                                {"$project": {"Projects.Tasks.projectID": 0,"Projects.Tasks.deadline": 0,"Projects.Tasks.joblist": 0,"Projects.Tasks.completionStatus": 0,}}
                            ]
        # employee_pipeline = [{"$match": {"_id": ObjectId(employee_id)}}]
        # broadcast_pipeline = [{"$match": {"_id": ObjectId(broadcast_id)}}]
        
        # employee_pipeline.extend(common_work_data_pipeline)
        # broadcast_pipeline.extend(common_work_data_pipeline)
        # employee_tasks = list(client.WorkBaseDB.Members.aggregate(employee_pipeline))
        # common_tasks = list(client.WorkBaseDB.Members.aggregate(broadcast_pipeline))
        work_details = list(client.WorkBaseDB.Members.aggregate(work_data_pipeline))
        # if len(employee_tasks) == 0 and len(common_tasks) == 0:
        if len(work_details) == 0:
            return make_response(jsonify({"message": "No Job Assignments Here Yet. Ask the Administrator to Assign you to a Project Activity"}), 400)
        # If the employee has no tasks, return the common tasks
        # if len(employee_tasks) == 0:
        #     employee_tasks = common_tasks
        # # If the employee has tasks, return the employee tasks
        # if len(common_tasks) != 0:
        #     # If the employee has tasks and common tasks, merge the common tasks with the employee tasks
        #     # For each employee task, add the common tasks to the employee tasks
        #     employee_tasks[0]['Projects'].extend(common_tasks[0]['Projects'])
        employee_tasks = work_details[0]['Projects']
        

        # replace projectID with project:{projectName: <ProjectName>, projectId: <ProjectID>} and taskID with task:{taskName: <TaskName>, taskId: <TaskID>} in the timesheet using the employee_tasks dictionary
        if 'Draft' in timesheets:
            for i in range(len(timesheets['Draft'])):
                for j in range(len(timesheets['Draft'][i]['employeeSheetObjects'])):
                    project_id = timesheets['Draft'][i]['employeeSheetObjects'][j].pop('projectID', None)
                    if project_id is not None:
                        for project in employee_tasks:
                            if project['_id'] == project_id:
                                timesheets['Draft'][i]['employeeSheetObjects'][j]['Project'] = dict({'projectID': project['_id'], 'projectName': project['name']})
                    task_id = timesheets['Draft'][i]['employeeSheetObjects'][j].pop('taskID', None)
                    if task_id is not None:
                        for project in employee_tasks:
                            for task in project['Tasks']:
                                if task['_id'] == task_id:
                                    timesheets['Draft'][i]['employeeSheetObjects'][j]['Task'] = dict({'taskID': task['_id'], 'taskName': task['name']})
            timesheets['Draft'] = sorted(timesheets['Draft'], key=lambda x: x['startDate'], reverse=True)
    
        # Convert the employee_sheets cursor object to a JSON object
        timesheets_json = json.dumps(timesheets, default=str)
        timesheets_data = json.loads(timesheets_json)
        # Return the JSON response
        return make_response(jsonify({"employeeSheets": timesheets_data}), 200)
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)


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
        timesheet_pipeline = [  {"$match": {"employeeID": ObjectId(employee_id)}},
                                {"$match": {"status": {"$in": ["Ongoing","Returned"]}}},
                                {"$group": {"_id": {"employeeID": "$employeeID","status": "$status"},
                                          "sheets": {"$push": {"employeeSheetID": "$_id","startDate": "$startDate","endDate": "$endDate","employeeSheetObjects": "$employeeSheetObject","Status": "$status","ReturnedMessage": "$returnMessage"}}}},
                                {"$group": {"_id": "$_id.employeeID","employeeSheet": {"$push": {"k": "$_id.status","v": "$sheets"}}}},
                                {"$replaceRoot": {"newRoot": {"$mergeObjects": [{ "$arrayToObject": "$employeeSheet" },{ "_id": "$_id" }]}}},
                                {"$project": {"_id": 0,"Ongoing": 1,"Returned": 1}}
                        ]
        timesheet_list = list(client.TimesheetDB.EmployeeSheets.aggregate(timesheet_pipeline))

        # return make_response(jsonify({"messages": "OK"}), 200)
        # Check if Timesheet list is empty
        if not timesheet_list:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)
        
        timesheets = timesheet_list[0]
        broadcast_id = client.WorkBaseDB.Members.find_one({"name": "ALL EMPLOYEES"})['_id']
        work_data_pipeline = [  {"$match": {"_id": {"$in": [ObjectId(employee_id),ObjectId(broadcast_id)]}}},
                                {"$lookup": {"from": "ProjectActivity","localField": "_id","foreignField": "activities.members","as": "matchingAssignments"}},
                                {"$unwind": "$matchingAssignments"},
                                {"$lookup": {"from": "Projects","localField": "matchingAssignments.projectID","foreignField": "_id","as": "matchingAssignments.project"}},
                                {"$unwind": "$matchingAssignments.project"},
                                {"$lookup": {"from": "Tasks","localField": "matchingAssignments.activities.tasks","foreignField": "_id","as": "matchingAssignments.task"}},
                                {"$unwind": "$matchingAssignments.task"},
                                {"$group": {"_id": {"employee_id": "$_id","project_id": "$matchingAssignments.project._id"},"project_name": { "$first": "$matchingAssignments.project.name" },"Tasks": { "$push": "$matchingAssignments.task" }}},
                                {"$group": {"_id": "$_id.employee_id","Projects": {"$push": {"_id": "$_id.project_id","name": "$project_name","Tasks": "$Tasks"}}}},
                                {"$project": {"_id": 0,"employeeID": "$_id","Projects": 1}},
                                {"$project": {"Projects.Tasks.projectID": 0,"Projects.Tasks.deadline": 0,"Projects.Tasks.joblist": 0,"Projects.Tasks.completionStatus": 0,}}
                            ]
        # employee_pipeline = [{"$match": {"_id": ObjectId(employee_id)}}]
        # broadcast_pipeline = [{"$match": {"_id": ObjectId(broadcast_id)}}]
        
        # employee_pipeline.extend(common_work_data_pipeline)
        # broadcast_pipeline.extend(common_work_data_pipeline)
        # employee_tasks = list(client.WorkBaseDB.Members.aggregate(employee_pipeline))
        # common_tasks = list(client.WorkBaseDB.Members.aggregate(broadcast_pipeline))
        work_details = list(client.WorkBaseDB.Members.aggregate(work_data_pipeline))
        # if len(employee_tasks) == 0 and len(common_tasks) == 0:
        if len(work_details) == 0:
            return make_response(jsonify({"message": "No Job Assignments Here Yet. Ask the Administrator to Assign you to a Project Activity"}), 400)
        # If the employee has no tasks, return the common tasks
        # if len(employee_tasks) == 0:
        #     employee_tasks = common_tasks
        # # If the employee has tasks, return the employee tasks
        # if len(common_tasks) != 0:
        #     # If the employee has tasks and common tasks, merge the common tasks with the employee tasks
        #     # For each employee task, add the common tasks to the employee tasks
        #     employee_tasks[0]['Projects'].extend(common_tasks[0]['Projects'])
        employee_tasks = work_details[0]['Projects']
        

        # replace projectID with project:{projectName: <ProjectName>, projectId: <ProjectID>} and taskID with task:{taskName: <TaskName>, taskId: <TaskID>} in the timesheet using the employee_tasks dictionary
        if 'Ongoing' in timesheets:
            for i in range(len(timesheets['Ongoing'])):
                for j in range(len(timesheets['Ongoing'][i]['employeeSheetObjects'])):
                    project_id = timesheets['Ongoing'][i]['employeeSheetObjects'][j].pop('projectID', None)
                    if project_id is not None:
                        for project in employee_tasks:
                            if project['_id'] == project_id:
                                timesheets['Ongoing'][i]['employeeSheetObjects'][j]['Project'] = dict({'projectID': project['_id'], 'projectName': project['name']})
                    task_id = timesheets['Ongoing'][i]['employeeSheetObjects'][j].pop('taskID', None)
                    if task_id is not None:
                        for project in employee_tasks:
                            for task in project['Tasks']:
                                if task['_id'] == task_id:
                                    timesheets['Ongoing'][i]['employeeSheetObjects'][j]['Task'] = dict({'taskID': task['_id'], 'taskName': task['name']})
            timesheets['Ongoing'] = sorted(timesheets['Ongoing'], key=lambda x: x['startDate'], reverse=True)
        if 'Returned' in timesheets:
            for i in range(len(timesheets['Returned'])):
                for j in range(len(timesheets['Returned'][i]['employeeSheetObjects'])):
                    project_id = timesheets['Returned'][i]['employeeSheetObjects'][j].pop('projectID', None)
                    if project_id is not None:
                        for project in employee_tasks:
                            if project['_id'] == project_id:
                                timesheets['Returned'][i]['employeeSheetObjects'][j]['Project'] = dict({'projectID': project['_id'], 'projectName': project['name']})
                    task_id = timesheets['Returned'][i]['employeeSheetObjects'][j].pop('taskID', None)
                    if task_id is not None:
                        for project in employee_tasks:
                            for task in project['Tasks']:
                                if task['_id'] == task_id:
                                    timesheets['Returned'][i]['employeeSheetObjects'][j]['Task'] = dict({'taskID': task['_id'], 'taskName': task['name']})
            timesheets['Returned'] = sorted(timesheets['Returned'], key=lambda x: x['startDate'], reverse=True)

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

def fetch_draft_timesheets(employee_uuid):
    """
    This function fetches all draft timesheets for an employee.
    It takes an employee ID as input.
    It returns a JSON response containing the draft timesheets or an error message.
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
            timesheets_response = get_draft_timesheets_for_employee(client, employee_id)  
            
            return timesheets_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def fetch_submitted_timesheets(employee_uuid):
    """
    This function fetches all submitted timesheets for an employee.
    It takes an employee ID as input.
    It returns a JSON response containing the submitted timesheets or an error message.
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
            timesheets_response = get_submitted_timesheets_for_employee(client, employee_id)  
            
            return timesheets_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

from datetime import datetime, timedelta
def get_current_week():
    '''
    This function calculates the date of the current Monday at midnight and the date of the next Monday at midnight.
    It returns the dates of the current Monday and the next Monday at midnight.
    '''
    current_date = datetime.now()  # Get the current date and time

    # Calculate the number of days until the next Monday
    # If today is Monday, set it to 1, else calculate the remaining days of the week
    # days_until_next_monday = 7 - current_date.weekday() if current_date.weekday() > 0 else 1

    current_monday = current_date - timedelta(days=current_date.weekday())  # Subtract the number of days until the next Monday from the current date

    # Get the date of the current Monday at midnight by replacing the hour, minute, second, and microsecond of current_monday with 0
    current_monday_midnight = current_monday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get the date of the next Monday at midnight by adding 7 days to current_monday_midnight
    next_monday_midnight = current_monday_midnight.replace(hour=23, minute=59, second=59 ) + timedelta(days=6)

    return current_monday_midnight, next_monday_midnight 

def employee_timesheet_operation(employee_uuid, timesheet):
    """
    This function creates a new timesheet for an employee.
    It takes the employee ID, timesheet data, and the collection to save to as input.
    It returns a JSON response containing the new timesheet or an error message.
    """
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        if isinstance(client, MongoClient):
            # correct data field formats for timesheet
            # check if the employeeID is valid
            verify = get_WorkAccount(client, employee_uuid)
            if not verify.status_code == 200:
                # If the connection fails, return the error response
                return verify
            employee_id= verify.json['_id']

            if timesheet is not None:
                employeSheetObjectList = []
                # store sheet to draft
                current_monday, next_monday = get_current_week()
                for employeesheetobject in timesheet['employeeSheetObjects']:
                    if 'projectID' not in employeesheetobject:
                        return make_response(jsonify({"error": "Project data is missing"}), 400)
                    if 'taskID' not in employeesheetobject:
                        return make_response(jsonify({"error": "Task data is missing"}), 400)
                    if 'billable' not in employeesheetobject:
                        return make_response(jsonify({"error": "Billable Data is missing"}), 400)
                    if 'workDay' not in employeesheetobject:
                        return make_response(jsonify({"error": "WorkDay data is missing"}), 400)
                    
                    # check if projectID is valid
                    verify = verify_attribute(collection=client.WorkBaseDB.Projects, key="_id",attr_value=employeesheetobject['projectID'])
                    if not verify:
                        return make_response(jsonify({"error": "Project data is incorrect"}), 400)
                    # check if taskID is valid
                    verify = verify_attribute(collection=client.WorkBaseDB.Tasks, key="_id",attr_value=employeesheetobject['taskID'])
                    if not verify:
                        return make_response(jsonify({"error": "Task data is incorrect"}), 400)
                    # check if workDay dataType is valid
                    if not isinstance(employeesheetobject['workDay'], dict):
                        return make_response(jsonify({"error": "WorkDay data is incorrect"}), 400)
                    
                    # Create WorkDay object
                    workDay = {
                        "mon": WorkDay(work=employeesheetobject["workDay"]["mon"]["work"], hour=employeesheetobject["workDay"]["mon"]["hour"], comment=employeesheetobject["workDay"]["mon"]["comment"]).to_dict(),
                        "tue": WorkDay(work=employeesheetobject["workDay"]["tue"]["work"], hour=employeesheetobject["workDay"]["tue"]["hour"], comment=employeesheetobject["workDay"]["tue"]["comment"]).to_dict(),
                        "wed": WorkDay(work=employeesheetobject["workDay"]["wed"]["work"], hour=employeesheetobject["workDay"]["wed"]["hour"], comment=employeesheetobject["workDay"]["wed"]["comment"]).to_dict(),
                        "thu": WorkDay(work=employeesheetobject["workDay"]["thu"]["work"], hour=employeesheetobject["workDay"]["thu"]["hour"], comment=employeesheetobject["workDay"]["thu"]["comment"]).to_dict(),
                        "fri": WorkDay(work=employeesheetobject["workDay"]["fri"]["work"], hour=employeesheetobject["workDay"]["fri"]["hour"], comment=employeesheetobject["workDay"]["fri"]["comment"]).to_dict(),
                        "sat": WorkDay(work=employeesheetobject["workDay"]["sat"]["work"], hour=employeesheetobject["workDay"]["sat"]["hour"], comment=employeesheetobject["workDay"]["sat"]["comment"]).to_dict(),
                        "sun": WorkDay(work=employeesheetobject["workDay"]["sun"]["work"], hour=employeesheetobject["workDay"]["sun"]["hour"], comment=employeesheetobject["workDay"]["sun"]["comment"]).to_dict()
                    }
                    
                    new_employeeSheetObject = EmployeeSheetObject(projectID=ObjectId(employeesheetobject['projectID']), taskID=ObjectId(employeesheetobject['taskID']), billable=employeesheetobject['billable'], workDay=workDay, description=employeesheetobject['description'])
                    employeSheetObjectList.append(new_employeeSheetObject)
                # create new timesheet
                # get manager of employee
                # return make_response(jsonify({"message": str(employeSheetObjectList)}), 200)
                managerID = client.WorkBaseDB.Members.find_one({"_id": ObjectId(employee_id)},{"managerID": "$reportsTo"})['managerID']
                if 'action' in timesheet:
                    if timesheet['action'].lower() == "draft": 
                        new_timesheet = EmployeeSheet(employeeID=ObjectId(employee_id), managerID=ObjectId(managerID), employeeSheetObject=employeSheetObjectList, startDate=current_monday, endDate=next_monday, status='Draft')
                        new_timesheet = client.TimesheetDB.EmployeeSheets.insert_one(new_timesheet.to_dict())
                        # Return the result message
                        return make_response(jsonify({"message": "Timesheet added as Draft"}), 200)           
                    elif timesheet['action'].lower() == "submit":
                        # check if same week has already submitted or reviewing timesheets
                        timesheet = client.TimesheetDB.EmployeeSheets.find_one({"employeeID": employee_id, "startDate": current_monday, "endDate": next_monday, "status": {"$in": ["Reviewing"]}})
                        if timesheet is not None:
                            return make_response(jsonify({"error": "Timesheet for this week already exists"}), 400)
                        # create new timesheet                        
                        new_timesheet = EmployeeSheet(employeeID=employee_id, managerID=managerID, employeeSheetObject=employeSheetObjectList, startDate=current_monday, endDate=next_monday, status='Reviewing')
                        new_timesheet = client.TimesheetDB.EmployeeSheets.insert_one(new_timesheet.to_dict())
                        # create manager Sheet Review object
                        # create new ManagerSheetReview document
                        managerSheetReview = ManagerSheetReview(status="Review", employeeSheetID=ObjectId(new_timesheet.inserted_id))
                        newManagerSheetReview = client.TimesheetDB.ManagerSheets.insert_one(managerSheetReview.to_dict())
                        # return make_response(jsonify({"message": str("OK")}), 200)
                        # update the TimesheetRecords for the new ManagerSheet, replacing the old ManagerSheet with the new one 
                        # create new managerSheetsInstance
                        # Add the new ManagerSheetReview document to the TimesheetRecords collection
                        document = client.TimesheetDB.TimesheetRecords.find_one({"managerID": managerID})
                        if document:
                            client.TimesheetDB.TimesheetRecords.update_one(
                                {"managerID": timesheet['managerID']},
                                {"$push": {"managerSheetsInstances": {
                                    "managerSheetsObjects": newManagerSheetReview.inserted_id,
                                    "lastUpdateDate": datetime.now(),
                                    "version": 0
                                }}}
                            )
                        else:
                            client.TimesheetDB.TimesheetRecords.insert_one({"managerID": managerID, "managerSheetsInstances": [{"managerSheetsObjects": newManagerSheetReview.inserted_id, "lastUpdateDate": datetime.now(), "version": 0}]})
                        # Return the result message
                        return make_response(jsonify({"message": "Timesheet Submitted for Review"}), 200)
                    else:
                        return make_response(jsonify({"error": "Illegal Action: Select Draft/Submit only"}), 400)
                else:
                    return make_response(jsonify({"error": "Action is required in payload"}), 400)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

# def save_timesheet(employee_uuid, timesheet):
#     """
#     This function saves a new timesheet for an employee.
#     It takes the employee ID, timesheet data, and the collection to save to as input.
#     It returns a JSON response containing the new timesheet or an error message.
#     """
#     try:
#         # Check the connection to the MongoDB server
#         client = dbConnectCheck()
#         if isinstance(client, MongoClient):
#             # correct data field formats for timesheet
#             # check if the employeeID is valid
#             verify = get_WorkAccount(client, employee_uuid)
#             if not verify.status_code == 200:
#                 # If the connection fails, return the error response
#                 return verify
#             employee_id= verify.json['_id']
#             if timesheet is not None:
#                 current_sheet = client.TimesheetDB.EmployeeSheets.find_one({"_id": timesheet['employeeSheetID']})
#                 if current_sheet is not None:
#                     # check if status update is valid:
#                     if current_sheet['status'] is not None:
#                         if current_sheet['status'] not in ["Draft", "Returned"]:
#                             return make_response(jsonify({"error": "Current sheet status does not allow changes"}), 400)
#                     # check if employeeSheetsID is valid
#                     if timesheet['employeeSheetID'] is not None:
#                         timesheet['employeeSheetID'] = ObjectId(timesheet['employeeSheetID'])
#                         verify = verify_attribute(collection=client.TimesheetDB.EmployeeSheets, key="_id",attr_value=timesheet['employeeSheetID'])
#                         if not verify:
#                             return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is incorrect"}), 400)
#                         verify = verify_attribute(collection=client.TimesheetDB.EmployeeSheets, key="employeeID",attr_value=employee_id)
#                         if not verify:
#                             return make_response(jsonify({"error": "employee doesnt has access to this timesheet "}), 400)
#                     else:
#                         return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is required"}), 400)
#                     # check if action is valid or not based on current sheet status
#                     if 'action' in timesheet:
#                         if timesheet['action'] not in ["Save", "Draft","Submit"]:
#                             return make_response(jsonify({"error": "Illegal Action: Select Draft/Save/Submit only"}), 400)
#                     else:
#                         return make_response(jsonify({"error": "timesheet 'status' data is required"}), 400)
                    
#                     # after all checks, now update the database
#                     # if action is Save or Draft, update the timesheet with the new employeeSheetObjects
#                     if current_sheet['status'] in ["Returned"]:
#                         if timesheet['action'] in ["Draft"]:
#                             # copy the timesheet with 'draft' as status in database
#                             client.TimesheetDB.EmployeeSheets.insert_one({"employeeID": employee_id, "status": "Draft", "employeeSheetObject": timesheet['employeeSheetObjects']})
#                             # Return the the message
#                             return make_response(jsonify({"message": "Timesheet added as Draft"}), 200)
#                         else:
#                             return make_response(jsonify({"error": "Illegal Action: Select Draft/Submit only"}), 400)
#                     elif current_sheet['status'] in ["Ongoing"]:
#                         if timesheet['action'] in ["Save"]:
#                             # update the sheet in database with the new employeeSheetObject
#                             client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet['employeeSheetID']}, {"$push": {"employeeSheetObject": timesheet['employeeSheetObjects']}})
#                             # Return the the message
#                             return make_response(jsonify({"message": "Timesheet saved successfully"}), 200)
#                         elif timesheet['action'] in ["Draft"]:
#                             # copy the timesheet with 'draft' as status in database
#                             client.TimesheetDB.EmployeeSheets.insert_one({"employeeID": employee_id, "status": "Draft", "employeeSheetObject": timesheet['employeeSheetObjects']})
#                             # Return the the message
#                             return make_response(jsonify({"message": "Timesheet added as Draft"}), 200)
#                         else:
#                             return make_response(jsonify({"error": "Illegal Action: Select Draft/Save only"}), 400)
#                     else:
#                         #
#                 else:
#                     return make_response(jsonify({"error": "Current sheet status does not allow changes"}), 400)
#         else:
#             # If the connection fails, return the error response
#             return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
#     except Exception as e:
#         # If an error occurs, return the error response
#         return make_response(jsonify({"error": str(e)}), 500)

def edit_timesheet(employee_uuid, timesheet):
    """
    This function edits an existing timesheet for an employee.
    It takes the employee ID, timesheet data, and the collection to save to as input.
    It returns a JSON response containing the updated timesheet or an error message.
    """
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()

        if isinstance(client, MongoClient):

            # correct data field formats for timesheet
            # check if the employeeID is valid
            verify = get_WorkAccount(client, employee_uuid)
            if not verify.status_code == 200:
                # If the connection fails, return the error response
                return verify
            employee_id= verify.json['_id']
            employee_id = "65c3fecb2b6c3e4c32082962"

            if timesheet is not None:
                # check if employeeSheetsID is valid
                current_sheet = client.TimesheetDB.EmployeeSheets.find_one({"_id": ObjectId(timesheet['employeeSheetID'])})
                if timesheet['employeeSheetID'] is not None:
                    timesheet['employeeSheetID'] = ObjectId(timesheet['employeeSheetID'])
                    verify = verify_attribute(collection=client.TimesheetDB.EmployeeSheets, key="_id",attr_value=timesheet['employeeSheetID'])
                    if not verify:
                        return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is incorrect"}), 400)
                    verify = verify_attribute(collection=client.TimesheetDB.EmployeeSheets, key="employeeID",attr_value=employee_id)
                    if not verify:
                        return make_response(jsonify({"error": "employee doesnt has access to this timesheet "}), 400)
                else:
                    return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is required"}), 400)
                # check if workDay records is valid
                if timesheet['workDay'] is not None and timesheet['workDay'] != {}:
                    for day, workDay in timesheet['workDay'].items():
                        timesheet['workDay'][day]['work'] = bool(workDay['work'])
                        timesheet['workDay'][day]['hour'] = int(workDay['hour'])
                        timesheet['workDay'][day]['comment'] = workDay['comment']
                else: 
                    return make_response(jsonify({"error": "timesheet 'workDay' data is required"}), 400)

                # employee can only update a day's hour data only on the same day and one day after when status is "Ongoing". Employee cant edit any future workDay details, or past workDay details other than past one day. employee can edit all days if status is "Returned". day's comment can be updated anytime while timesheet is available
                # get the current timesheet for comparison
                if current_sheet['status'] == "Ongoing":
                    # get list of workdays which were updated
                    updated_days = [day for day in timesheet["workDay"] if timesheet["workDay"][day]['hour'] != current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]['hour']]
                    updated_overall_days = [day for day in timesheet["workDay"] if timesheet["workDay"][day] != current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]]
                    if len(updated_overall_days) == 0:
                        return make_response(jsonify({"error": "No workDay details updated"}), 400)
                    
                    # return make_response(jsonify({"message": "working"}), 200)
                    # define acceptable days for updating
                    days_of_week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                    current_day_index = days_of_week.index(datetime.today().strftime('%a').lower())
                    acceptable_days = [days_of_week[current_day_index], days_of_week[current_day_index - 1]]
                    print("Current Day: %d" % current_day_index)
                    print("Acceptable Days: %s" % acceptable_days)
                    print("Updated Days: %s" % updated_days)

                    # check if all updated days in original timesheet have work set to True
                    for day in updated_days:
                        if current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]["work"] == False:
                            return make_response(jsonify({"error": "Cannot update a non-work day"}), 400)
                        if day not in acceptable_days:
                            return make_response(jsonify({"error": "You can only fill details of Today and Yesterday"}), 400)

                    # else, update the hour and comment for the latest instance of employeeSheetInstance at employeeSheetObject
                    [client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet['employeeSheetID'], "employeeSheetInstances": {"$elemMatch": {"version": current_sheet['employeeSheetInstances'][-1]["version"]}}}, {"$set": {"employeeSheetInstances.$.employeeSheetObject.workDay."+day: timesheet['workDay'][day]}}) for day in days_of_week]
        
                elif current_sheet['status'] == "Returned":
                    # get list of workdays which were updated
                    updated_days = [day for day in timesheet["workDay"] if timesheet["workDay"][day]['hour'] != current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]['hour']]
                    updated_comments = [day for day in timesheet["workDay"] if timesheet["workDay"][day]['comment'] != current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]['comment']]
                    updated_overall_days = [day for day in timesheet["workDay"] if timesheet["workDay"][day] != current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]]
                    if len(updated_overall_days) == 0:
                        return make_response(jsonify({"error": "No workDay details updated"}), 400)
                    elif len(updated_days) == 0 and len(updated_comments) !=0:
                        return make_response(jsonify({"error": "Comments added successfully"}), 200)
                    # check if all updated days in original timesheet have work set to True
                    for day in updated_days:
                        if current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]["work"] == False:
                            return make_response(jsonify({"error": "Cannot update a non-work day"}), 400)
                    
                    days_of_week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                    # else, update the hour and comment for the latest instance of employeeSheetInstance at employeeSheetObject
                    [client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet['employeeSheetID'], "employeeSheetInstances": {"$elemMatch": {"version": current_sheet['employeeSheetInstances'][-1]["version"]}}}, 
                                                                  {"$set": {"employeeSheetInstances.$.employeeSheetObject.workDay."+day: timesheet['workDay'][day],
                                                                            "status": "Reviewing"}}) for day in days_of_week]

                else:
                    return make_response(jsonify({"error": "Status of timesheet is incorrect"}), 400)
                
                # after successful action, return message Day's work update successful
                return make_response(jsonify({"message": "Day's work update successful"}), 200)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def get_employee_assignments(employee_id):
    """
    Retrieves all tasks for an employee from the database.

    Args:
        employee_id (str): The ID of the employee.

    Returns:
        JSON response: A JSON response containing the tasks or an error message.
    """
    try:
        client = dbConnectCheck() 
        if isinstance(client, MongoClient):
            # Use aggregation pipeline to match the employee ID and project the required fields
            broadcast_id = client.WorkBaseDB.Members.find_one({"name": "ALL EMPLOYEES"})['_id']
            work_data_pipeline = [  {"$match": {"_id": {"$in": [ObjectId(employee_id),ObjectId(broadcast_id)]}}},
                                {"$lookup": {"from": "ProjectActivity","localField": "_id","foreignField": "activities.members","as": "matchingAssignments"}},
                                {"$unwind": "$matchingAssignments"},
                                {"$lookup": {"from": "Projects","localField": "matchingAssignments.projectID","foreignField": "_id","as": "matchingAssignments.project"}},
                                {"$unwind": "$matchingAssignments.project"},
                                {"$lookup": {"from": "Tasks","localField": "matchingAssignments.activities.tasks","foreignField": "_id","as": "matchingAssignments.task"}},
                                {"$unwind": "$matchingAssignments.task"},
                                {"$group": {"_id": {"employee_id": "$_id","project_id": "$matchingAssignments.project._id"},"project_name": { "$first": "$matchingAssignments.project.name" },"Tasks": { "$push": "$matchingAssignments.task" }}},
                                {"$group": {"_id": "$_id.employee_id","Projects": {"$push": {"_id": "$_id.project_id","name": "$project_name","Tasks": "$Tasks"}}}},
                                {"$project": {"_id": 0,"employeeID": "$_id","Projects": 1}},
                                {"$project": {"Projects.Tasks.projectID": 0,"Projects.Tasks.deadline": 0,"Projects.Tasks.joblist": 0,"Projects.Tasks.completionStatus": 0,}}
                            ]
            # employee_pipeline = [{"$match": {"_id": ObjectId(employee_id)}}]
            # broadcast_pipeline = [{"$match": {"_id": ObjectId(broadcast_id)}}]
            
            # employee_pipeline.extend(common_work_data_pipeline)
            # broadcast_pipeline.extend(common_work_data_pipeline)

            # employee_tasks = list(client.WorkBaseDB.Members.aggregate(employee_pipeline))
            # common_tasks = list(client.WorkBaseDB.Members.aggregate(broadcast_pipeline))
            work_details = list(client.WorkBaseDB.Members.aggregate(work_data_pipeline))
            # if len(employee_tasks) == 0 and len(common_tasks) == 0:
            if len(work_details) == 0:
                # Convert the employee_sheets cursor object to a JSON object
                return make_response(jsonify({"message": "No Job Assignments Here Yet. Ask the Administrator to Assign you to a Project Activity"}), 400)
            # If the employee has no tasks, return the common tasks
            # if len(employee_tasks) == 0:
            #     employee_tasks = common_tasks
            # # If the employee has tasks, return the employee tasks
            # if len(common_tasks) != 0:
            #     # If the employee has tasks and common tasks, merge the common tasks with the employee tasks
            #     # For each employee task, add the common tasks to the employee tasks
            #     employee_tasks[0]['Projects'].extend(common_tasks[0]['Projects'])
            employee_tasks = work_details
            # Convert the employee_sheets cursor object to a JSON object
            tasks_json = json.dumps(employee_tasks[0], default=str)
            tasks_data = json.loads(tasks_json)
            # Return the JSON response
            return make_response(jsonify({"employeeTasks": tasks_data}), 200)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def fetch_employee_project_tasks(employee_uuid):
    """
    This function fetches all tasks for an employee.
    It takes an employee ID as input.y
    It returns a JSON response containing the tasks or an error message.
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
            
            employee_id = verify.json["_id"]
            # Call the get_tasks_for_employee function with the employee ID
            tasks_response = get_employee_assignments(employee_id)  
            return tasks_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)