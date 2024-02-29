# Import necessary modules
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
# import threading
from bson import ObjectId
from flask import Flask, jsonify, make_response
from pymongo import MongoClient
import os
# from dotenv import load_dotenv, find_dotenv
import json
from ...models import ManagerSheetsAssign,ManagerSheetsInstance,WorkDay
from ....connectors.dbConnector import dbConnectCheck, get_WorkAccount, verify_attribute
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
        # Use aggregation pipeline to match the employee ID and project the required fields
        default_pipeline = [
                            {"$match": {"managerID": ObjectId(manager_id)}},
                            {"$unwind": "$managerSheetsInstances"},
                            {"$lookup": {
                                "from": "ManagerSheets",
                                "localField": "managerSheetsInstances.managerSheetsObjects",
                                "foreignField": "_id",
                                "as": "managerSheets"}},
                            {"$match": {"managerSheets.status": { "$ne": "Review" }}},
                            {"$unwind": "$managerSheets"},
                            {"$lookup": {
                                "from": "AssignmentGroup",
                                "localField": "managerSheets.assignGroupID",
                                "foreignField": "_id",
                                "as": "assignGroup"}},
                            {"$unwind": "$assignGroup"},
                            {"$project": {"managerSheetID": "$managerSheets._id",
                                        "Last Update Date": "$managerSheetsInstances.lastUpdateDate",
                                        "Sheet Version": "$managerSheetsInstances.version",
                                        "Project": "$assignGroup.projectID",
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
                                        "Assignee": "$assignGroup",
                                        }},
                            
                            ]
        review_pipeline = [
                            {"$match": {"managerID": ObjectId(manager_id)}},
                            {"$unwind": "$managerSheetsInstances"},
                            {"$lookup": {
                                "from": "ManagerSheets",
                                "localField": "managerSheetsInstances.managerSheetsObjects",
                                "foreignField": "_id",
                                "as": "managerSheets"}},
                            {"$match": {"managerSheets.status": "Review"}},
                            {"$unwind": "$managerSheets"},
                            {"$lookup": {
                              "from": "EmployeeSheets",
                              "localField": "managerSheets.employeeSheetID",
                              "foreignField": "_id",
                              "as": "employeeSheets"}},
                            {"$match": {"employeeSheets.status": "Reviewing"}},
                            {"$unwind": "$employeeSheets"},
                            {"$project": {
                              "managerSheetID": "$managerSheets._id",
                              "employeeSheetID": "$employeeSheets._id",
                              "Employee": "$employeeSheets.employeeID",
                              "startDate": "$employeeSheets.startDate",
                              "endDate": "$employeeSheets.endDate",
                              "Status": "$managerSheets.status",
                              "submittedSheets": "$employeeSheets.employeeSheetObject"
                              }}
                            ]

        # Check the status of the timesheets
        if status == "Draft" or status == "Assign":
            timesheets = list(client.TimesheetDB.TimesheetRecords.aggregate(default_pipeline))
        elif status == "Review":
            timesheets = list(client.TimesheetDB.TimesheetRecords.aggregate(review_pipeline))
        
        # Check if Timesheet Exists
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
                            # {"$match": {"Employee.employeeID": ObjectId(manager_id)}}
                        ]
        work = list(client.WorkBaseDB.Assignments.aggregate(work_pipeline))
        assign_pipeline = [{
                            "$lookup": {
                              "from": "Members",
                              "localField": "assignedTo",
                              "foreignField": "_id",
                              "as": "assignedTo"
                            }
                          },
                          {
                            "$addFields": {
                              "assignedMembers": {
                                "$map": {
                                  "input": "$assignedTo",
                                  "as": "member",
                                  "in": {
                                    "_id": "$$member._id",
                                    "name": "$$member.name"
                                  }
                                }
                              }
                            }
                          },
                        {
                            "$project": {
                              "_id": 0,
                            "assignmentID": "$_id",
                            "name": 1,
                            "assignedMembers": 1
                            }
                          },
                        ]
        assign = list(client.WorkBaseDB.Assignments.aggregate(assign_pipeline))
        

        filtered_timesheets = []
        if status == "Draft":
            query = ["Draft"]
        # is statuses of timesheets is manage, select Active, Upcoming, and review
        elif status == "Assign":
            query = ["Active", "Upcoming"]
        elif status == "Review":
            query = ["Review"]

        for ts in timesheets:
            if ts.get('Status') in query:
                filtered_timesheets.append(ts)
        
        project_dict= {item['Project']['projectID']: item['Project'] for item in work}
        employee_dict= {item['Employee']['employeeID']: item['Employee'] for item in work}
        task_dict= {item['Task']['taskID']: item['Task'] for item in work}
        assign_dict= {item['assignmentID']: item for item in assign}
        if status == "Draft" or status == "Assign":
            for i in range(len(filtered_timesheets)):
                project_id = filtered_timesheets[i]['Project']
                project_item = project_dict.get(project_id)
                if project_item:
                    # Merge Project details
                    filtered_timesheets[i]['Project'] = project_item
            
                # Iterate over assignmentInstances in Assignee
                for j in range(len(filtered_timesheets[i]['Assignee']['assignmentInstances'])):
                    assign_id = filtered_timesheets[i]['Assignee']['assignmentInstances'][j].pop('assignmentID', None)
                    if assign_id is not None:
                      assign_item = assign_dict.get(assign_id)
                      if assign_item:
                          # Replace assignmentID with the corresponding item from the new pipeline
                          filtered_timesheets[i]['Assignee']['assignmentInstances'][j]['Assignment'] = assign_item
        elif status == 'Review':
            for i in range(len(filtered_timesheets)):
                employee_id = filtered_timesheets[i]['Employee']
                employee_item = employee_dict.get(employee_id)
                print(employee_item)
                if employee_item:
                    # Merge Project details
                    filtered_timesheets[i]['Employee'] = employee_item
                for j in range(len(filtered_timesheets[i]['submittedSheets'])):
                    project_id = filtered_timesheets[i]['submittedSheets'][j].pop('projectID', None)
                    if project_id is not None:
                        project_item = project_dict.get(project_id)
                        if project_item:
                            filtered_timesheets[i]['submittedSheets'][j]['Project'] = project_item
                    task_id = filtered_timesheets[i]['submittedSheets'][j].pop('taskID', None)
                    if task_id is not None:
                        task_item = task_dict.get(task_id)
                        if task_item:
                            filtered_timesheets[i]['submittedSheets'][j]['Task'] = task_item

        # Check if Timesheet list is empty
        if not filtered_timesheets:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # sort the sheets by their startDate
        # if status == "Draft" or status == "Upcoming" or status == "Active":
        #     startDate = "Start Date"
        # elif status == "Review":
        #     startDate = "startDate"
        filtered_timesheets = sorted(filtered_timesheets, key=lambda x: x["startDate"])

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
            # timesheets_response = get_timesheets_for_manager(client, ObjectId("65c409092b6c3e4c3208296f"), status)  
            
            return timesheets_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def get_review_timesheets_for_manager(client, manager_id):
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
        # Use aggregation pipeline to match the employee ID and project the required fields
        pipeline = [
                    {"$match": {"managerID": ObjectId(manager_id)}},
                    {"$unwind": "$managerSheetsInstances"},
                    {"$lookup": {
                        "from": "ManagerSheets",
                        "localField": "managerSheetsInstances.managerSheetsObjects",
                        "foreignField": "_id",
                        "as": "managerSheets"}},
                    {"$match": {"managerSheets.status": "Review"}},
                    {"$unwind": "$managerSheets"},
                    {"$lookup": {
                      "from": "EmployeeSheets",
                      "localField": "managerSheets.employeeSheetID",
                      "foreignField": "_id",
                      "as": "employeeSheets"}},
                    {"$match": {"employeeSheets.status": "Reviewing"}},
                    {"$unwind": "$employeeSheets"},
                    {"$project": {
                      "managerSheetID": "$managerSheets._id",
                      "employeeSheetID": "$employeeSheets._id",
                      "Employee": "$employeeSheets.employeeID",
                      "startDate": "$employeeSheets.startDate",
                      "endDate": "$employeeSheets.endDate",
                      "Status": "$managerSheets.status",
                      "employeeSheetObjects": "$employeeSheets.employeeSheetObject"
                      }}
                    ]

        # Check the status of the timesheets
        timesheets = list(client.TimesheetDB.TimesheetRecords.aggregate(pipeline))
        
        # Check if Timesheet Exists
        if len(timesheets) == 0:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)
        
        # work_pipeline = [
        #                     {"$unwind": "$assignedTo",},
        #                     {"$lookup": {"from": "Members",
        #                                 "localField": "assignedTo",
        #                                 "foreignField": "_id",
        #                                 "as": "member"}},
        #                     {"$unwind": "$member"},
        #                     {"$lookup": {"from": "Members",
        #                                 "localField": "assignedBy",
        #                                 "foreignField": "_id",
        #                                 "as": "manager"}},
        #                     {"$unwind": "$manager"},
        #                     {"$lookup": {"from": "Tasks",
        #                                 "localField": "taskID",
        #                                 "foreignField": "_id",
        #                                 "as": "task"}},
        #                     {"$unwind": "$task"},
        #                     {"$lookup": {"from": "Projects",
        #                                 "localField": "task.projectID",
        #                                 "foreignField": "_id",
        #                                 "as": "project"}},
        #                     {"$unwind": "$project"},
        #                     {"$project": {"Assignment Name": "$name",
        #                                     "Project": {"projectID": "$project._id",
        #                                                 "Project Name": "$project.name"},
        #                                     "Task": {"taskID": "$task._id",
        #                                             "Task Name": "$task.name",
        #                                             "Billable": "$task.billable",
        #                                             "Task Description": "$task.description"},
        #                                     "Employee": {"employeeID": "$member._id",
        #                                                 "Employee Name": "$member.name"},
        #                                     "Manager": {"managerID": "$manager._id",
        #                                                 "Manager Name": "$manager.name"}}},
                            # {"$match": {"Employee.employeeID": ObjectId(manager_id)}}
        # work = list(client.WorkBaseDB.Assignments.aggregate(work_pipeline))
        # assign_pipeline = [{
        #                     "$lookup": {
        #                       "from": "Members",
        #                       "localField": "assignedTo",
        #                       "foreignField": "_id",
        #                       "as": "assignedTo"
        #                     }
        #                   },
        #                   {
        #                     "$addFields": {
        #                       "assignedMembers": {
        #                         "$map": {
        #                           "input": "$assignedTo",
        #                           "as": "member",
        #                           "in": {
        #                             "_id": "$$member._id",
        #                             "name": "$$member.name"
        #                           }
        #                         }
        #                       }
        #                     }
        #                   },
        #                 {
        #                     "$project": {
        #                       "_id": 0,
        #                     "assignmentID": "$_id",
        #                     "name": 1,
        #                     "assignedMembers": 1
        #                     }
        #                   },
        #                 ]
        # assign = list(client.WorkBaseDB.Assignments.aggregate(assign_pipeline))

        # filtered_timesheets = timesheets
        # project_dict= {item['Project']['projectID']: item['Project'] for item in work}
        # employee_dict= {item['Employee']['employeeID']: item['Employee'] for item in work}
        # task_dict= {item['Task']['taskID']: item['Task'] for item in work}
        # assign_dict= {item['assignmentID']: item for item in assign}
        # for i in range(len(filtered_timesheets)):
        #     employee_id = filtered_timesheets[i]['Employee']
        #     employee_item = employee_dict.get(employee_id)
        #     if employee_item:
        #         # Merge Project details
        #         filtered_timesheets[i]['Employee'] = employee_item
        #     for j in range(len(filtered_timesheets[i]['submittedSheets'])):
        #         project_id = filtered_timesheets[i]['submittedSheets'][j].pop('projectID', None)
        #         if project_id is not None:
        #             project_item = project_dict.get(project_id)
        #             if project_item:
        #                 filtered_timesheets[i]['submittedSheets'][j]['Project'] = project_item
        #         task_id = filtered_timesheets[i]['submittedSheets'][j].pop('taskID', None)
        #         if task_id is not None:
        #             task_item = task_dict.get(task_id)
        #             if task_item:
        #                 filtered_timesheets[i]['submittedSheets'][j]['Task'] = task_item

        activity_pipeline = [
                                {"$lookup": {"from": "Projects", "localField": "projectID", "foreignField": "_id", "as": "project"}},
                                {"$unwind": "$project"},
                                {"$lookup": {"from": "Tasks", "localField": "activities.tasks", "foreignField": "_id", "as": "task"}},
                                {"$unwind": "$task"},
                                {"$lookup": {"from": "Members", "localField": "activities.members", "foreignField": "_id", "as": "employees"}},
                                {"$group": {"_id": "$project._id", "projectName": {"$first": "$project.name"}, "Tasks": {"$push": "$task"}, "Employees": {"$first": "$employees"}}},
                                {"$project": {"_id": 0, "Project": {"projectID": "$_id", "projectName": "$projectName", "Tasks": "$Tasks", "Employees": "$Employees"}}},
                                {"$addFields": {"Project.Tasks": {"$map": {"input": "$Project.Tasks","as": "task","in": {"taskID": "$$task._id","taskName": "$$task.name","billable": "$$task.billable"}}},
                                                "Project.Employees": {"$map": {"input": "$Project.Employees","as": "employee","in": {"employeeID": "$$employee._id","employeeName": "$$employee.name","role": "$$employee.role"}}}}},
                                {"$project": {"Project.projectID": 1,"Project.projectName": 1,"Project.Tasks.taskID": 1,"Project.Tasks.taskName": 1,"Project.Tasks.billable": 1,"Project.Employees.employeeID": 1,"Project.Employees.employeeName": 1,"Project.Employees.role": 1}}
                            ]

        activity = list(client.WorkBaseDB.ProjectActivity.aggregate(activity_pipeline))

        filtered_timesheets = timesheets

        # replace projectID with project:{projectName: <ProjectName>, projectId: <ProjectID>} and taskID with task:{taskName: <TaskName>, taskId: <TaskID>} and employeeID with employee:{employeeName: <EmployeeName>, employeeId: <employeeIDID>} in the timesheet using the employee_tasks dictionary
        # Create dictionaries for projects and tasks

        projects_dict = {project['Project']['projectID']: project['Project']['projectName'] for project in activity}
        tasks_dict = {task['taskID']: task['taskName'] for project in activity for task in project['Project']['Tasks']}
        employees_dict = {employee['employeeID']: employee['employeeName'] for project in activity for employee in project['Project']['Employees']}

       # Replace projectID and taskID in timesheets
        for timesheet in filtered_timesheets:
            employee_id = timesheet.pop('Employee', None)
            if employee_id is not None and employee_id in employees_dict:
                timesheet['Employee'] = {'employeeID': employee_id, 'employeeName': employees_dict[employee_id]}
            else:
                timesheet['Employee'] = {'employeeID': employee_id, 'employeeName': "Employee not found"}
            for obj in timesheet['employeeSheetObjects']:
                project_id = obj.pop('projectID', None)
                if project_id is not None and project_id in projects_dict:
                    obj['Project'] = {'projectID': project_id, 'projectName': projects_dict[project_id]}
                else:
                    obj['Project'] = {'projectID': project_id, 'projectName': "Project not found"}
                task_id = obj.pop('taskID', None)
                if task_id is not None and task_id in tasks_dict:
                    obj['Task'] = {'taskID': task_id, 'taskName': tasks_dict[task_id]}
                else:
                    obj['Task'] = {'taskID': task_id, 'taskName': "Task not found"}
        # sort the sheets based on employee name
        filtered_timesheets = sorted(filtered_timesheets, key=lambda x: x["Employee"])
        
        # return make_response(jsonify({"data": str(filtered_timesheets)}), 200)

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

def fetch_review_timesheets(manager_uuid):
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
            timesheets_response = get_review_timesheets_for_manager(client, manager_id)  
            # timesheets_response = get_timesheets_for_manager(client, ObjectId("65c409092b6c3e4c3208296f"), status)  
            
            return timesheets_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def get_submitted_timesheets_for_manager(client, manager_id):
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
        # Use aggregation pipeline to match the employee ID and project the required fields
        pipeline = [
                    {"$match": {"managerID": ObjectId(manager_id)}},
                    {"$unwind": "$managerSheetsInstances"},
                    {"$lookup": {
                        "from": "ManagerSheets",
                        "localField": "managerSheetsInstances.managerSheetsObjects",
                        "foreignField": "_id",
                        "as": "managerSheets"}},
                    {"$match": {"managerSheets.status": "Submitted"}},
                    {"$unwind": "$managerSheets"},
                    {"$lookup": {
                      "from": "EmployeeSheets",
                      "localField": "managerSheets.employeeSheetID",
                      "foreignField": "_id",
                      "as": "employeeSheets"}},
                    {"$match": {"employeeSheets.status": "Submitted"}},
                    {"$unwind": "$employeeSheets"},
                    {"$project": {
                      "managerSheetID": "$managerSheets._id",
                      "employeeSheetID": "$employeeSheets._id",
                      "Employee": "$employeeSheets.employeeID",
                      "startDate": "$employeeSheets.startDate",
                      "endDate": "$employeeSheets.endDate",
                      "Status": "$managerSheets.status",
                      "employeeSheetObjects": "$employeeSheets.employeeSheetObject"
                      }}
                    ]

        # Check the status of the timesheets
        timesheets = list(client.TimesheetDB.TimesheetRecords.aggregate(pipeline))
        
        # Check if Timesheet Exists
        if len(timesheets) == 0:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)
        
        # work_pipeline = [
        #                     {"$unwind": "$assignedTo",},
        #                     {"$lookup": {"from": "Members",
        #                                 "localField": "assignedTo",
        #                                 "foreignField": "_id",
        #                                 "as": "member"}},
        #                     {"$unwind": "$member"},
        #                     {"$lookup": {"from": "Members",
        #                                 "localField": "assignedBy",
        #                                 "foreignField": "_id",
        #                                 "as": "manager"}},
        #                     {"$unwind": "$manager"},
        #                     {"$lookup": {"from": "Tasks",
        #                                 "localField": "taskID",
        #                                 "foreignField": "_id",
        #                                 "as": "task"}},
        #                     {"$unwind": "$task"},
        #                     {"$lookup": {"from": "Projects",
        #                                 "localField": "task.projectID",
        #                                 "foreignField": "_id",
        #                                 "as": "project"}},
        #                     {"$unwind": "$project"},
        #                     {"$project": {"Assignment Name": "$name",
        #                                     "Project": {"projectID": "$project._id",
        #                                                 "Project Name": "$project.name"},
        #                                     "Task": {"taskID": "$task._id",
        #                                             "Task Name": "$task.name",
        #                                             "Billable": "$task.billable",
        #                                             "Task Description": "$task.description"},
        #                                     "Employee": {"employeeID": "$member._id",
        #                                                 "Employee Name": "$member.name"},
        #                                     "Manager": {"managerID": "$manager._id",
        #                                                 "Manager Name": "$manager.name"}}},
                            # {"$match": {"Employee.employeeID": ObjectId(manager_id)}}
        # work = list(client.WorkBaseDB.Assignments.aggregate(work_pipeline))
        # assign_pipeline = [{
        #                     "$lookup": {
        #                       "from": "Members",
        #                       "localField": "assignedTo",
        #                       "foreignField": "_id",
        #                       "as": "assignedTo"
        #                     }
        #                   },
        #                   {
        #                     "$addFields": {
        #                       "assignedMembers": {
        #                         "$map": {
        #                           "input": "$assignedTo",
        #                           "as": "member",
        #                           "in": {
        #                             "_id": "$$member._id",
        #                             "name": "$$member.name"
        #                           }
        #                         }
        #                       }
        #                     }
        #                   },
        #                 {
        #                     "$project": {
        #                       "_id": 0,
        #                     "assignmentID": "$_id",
        #                     "name": 1,
        #                     "assignedMembers": 1
        #                     }
        #                   },
        #                 ]
        # assign = list(client.WorkBaseDB.Assignments.aggregate(assign_pipeline))

        # filtered_timesheets = timesheets
        # project_dict= {item['Project']['projectID']: item['Project'] for item in work}
        # employee_dict= {item['Employee']['employeeID']: item['Employee'] for item in work}
        # task_dict= {item['Task']['taskID']: item['Task'] for item in work}
        # assign_dict= {item['assignmentID']: item for item in assign}
        # for i in range(len(filtered_timesheets)):
        #     employee_id = filtered_timesheets[i]['Employee']
        #     employee_item = employee_dict.get(employee_id)
        #     if employee_item:
        #         # Merge Project details
        #         filtered_timesheets[i]['Employee'] = employee_item
        #     for j in range(len(filtered_timesheets[i]['submittedSheets'])):
        #         project_id = filtered_timesheets[i]['submittedSheets'][j].pop('projectID', None)
        #         if project_id is not None:
        #             project_item = project_dict.get(project_id)
        #             if project_item:
        #                 filtered_timesheets[i]['submittedSheets'][j]['Project'] = project_item
        #         task_id = filtered_timesheets[i]['submittedSheets'][j].pop('taskID', None)
        #         if task_id is not None:
        #             task_item = task_dict.get(task_id)
        #             if task_item:
        #                 filtered_timesheets[i]['submittedSheets'][j]['Task'] = task_item

        activity_pipeline = [
                                {"$lookup": {"from": "Projects", "localField": "projectID", "foreignField": "_id", "as": "project"}},
                                {"$unwind": "$project"},
                                {"$lookup": {"from": "Tasks", "localField": "activities.tasks", "foreignField": "_id", "as": "task"}},
                                {"$unwind": "$task"},
                                {"$lookup": {"from": "Members", "localField": "activities.members", "foreignField": "_id", "as": "employees"}},
                                {"$group": {"_id": "$project._id", "projectName": {"$first": "$project.name"}, "Tasks": {"$push": "$task"}, "Employees": {"$first": "$employees"}}},
                                {"$project": {"_id": 0, "Project": {"projectID": "$_id", "projectName": "$projectName", "Tasks": "$Tasks", "Employees": "$Employees"}}},
                                {"$addFields": {"Project.Tasks": {"$map": {"input": "$Project.Tasks","as": "task","in": {"taskID": "$$task._id","taskName": "$$task.name","billable": "$$task.billable"}}},
                                                "Project.Employees": {"$map": {"input": "$Project.Employees","as": "employee","in": {"employeeID": "$$employee._id","employeeName": "$$employee.name","role": "$$employee.role"}}}}},
                                {"$project": {"Project.projectID": 1,"Project.projectName": 1,"Project.Tasks.taskID": 1,"Project.Tasks.taskName": 1,"Project.Tasks.billable": 1,"Project.Employees.employeeID": 1,"Project.Employees.employeeName": 1,"Project.Employees.role": 1}}
                            ]

        activity = list(client.WorkBaseDB.ProjectActivity.aggregate(activity_pipeline))

        filtered_timesheets = timesheets

        # replace projectID with project:{projectName: <ProjectName>, projectId: <ProjectID>} and taskID with task:{taskName: <TaskName>, taskId: <TaskID>} and employeeID with employee:{employeeName: <EmployeeName>, employeeId: <employeeIDID>} in the timesheet using the employee_tasks dictionary
        # Create dictionaries for projects and tasks

        projects_dict = {project['Project']['projectID']: project['Project']['projectName'] for project in activity}
        tasks_dict = {task['taskID']: task['taskName'] for project in activity for task in project['Project']['Tasks']}
        employees_dict = {employee['employeeID']: employee['employeeName'] for project in activity for employee in project['Project']['Employees']}

       # Replace projectID and taskID in timesheets
        for timesheet in filtered_timesheets:
            employee_id = timesheet.pop('Employee', None)
            if employee_id is not None and employee_id in employees_dict:
                timesheet['Employee'] = {'employeeID': employee_id, 'employeeName': employees_dict[employee_id]}
            else:
                timesheet['Employee'] = {'employeeID': employee_id, 'employeeName': "Employee not found"}
            for obj in timesheet['employeeSheetObjects']:
                project_id = obj.pop('projectID', None)
                if project_id is not None and project_id in projects_dict:
                    obj['Project'] = {'projectID': project_id, 'projectName': projects_dict[project_id]}
                else:
                    obj['Project'] = {'projectID': project_id, 'projectName': "Project not found"}
                task_id = obj.pop('taskID', None)
                if task_id is not None and task_id in tasks_dict:
                    obj['Task'] = {'taskID': task_id, 'taskName': tasks_dict[task_id]}
                else:
                    obj['Task'] = {'taskID': task_id, 'taskName': "Task not found"}
        # sort the sheets based on employee name
        filtered_timesheets = sorted(filtered_timesheets, key=lambda x: x["Employee"])
        
        # return make_response(jsonify({"data": str(filtered_timesheets)}), 200)

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

def fetch_submitted_timesheets(manager_uuid):
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
            timesheets_response = get_submitted_timesheets_for_manager(client, manager_id) 
            
            return timesheets_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def store_timesheet_object(args):
    duration, projectID, workDay, description, status, assignGroupID, manager_id = args['duration'], args['projectID'], args['workDay'], args['description'], args['status'], args['assignGroupID'], args['manager_id']
    client = dbConnectCheck()  # create a new MongoClient instance for this thread
    startDate = datetime.strptime(duration['startDate'], "%Y-%m-%d %H:%M:%S")
    endDate = datetime.strptime(duration['endDate'], "%Y-%m-%d %H:%M:%S")
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
            return make_response(jsonify({"error": "Illegal Action for timesheet. Action must be 'Save' or 'Draft'"}), 400)
        status=""
        success_message=""
        if action == "Draft":
            status = "Draft"
            success_message = {"message": "Timesheet saved to Draft successfully"}
        elif action == "Save":
            success_message = {"message": "Timesheet assigned successfully"}
        
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

        # if endDate is not a sunday before midnight, then we need to set it to next sunDay before midnight
        if endDate.weekday() != 6:
            endDate = endDate + timedelta(days=(6 - endDate.weekday()))
            endDate = datetime(endDate.year, endDate.month, endDate.day, 23, 59, 59)

        # if endDate and startDate are within the same week [mon-sun], then alright. But, if they exceed, then we need to break down the timesheet into multiple timesheets with each one within each week
        # print the hours and minutes of the times too. final setting of each end date should be the day and time is 23:59:59
        def storeDates(startDate, endDate):
            dates = []
            
            def printWeekOrNot(startDate, endDate):
                endDate = endDate.replace(hour=23, minute=59, second=59)
                if startDate.weekday() == 0 and endDate.weekday() == 6:
                    dates.append({'startDate': startDate.strftime("%Y-%m-%d %H:%M:%S"), 'endDate': endDate.strftime("%Y-%m-%d %H:%M:%S")})
                else:
                    dates.append({'startDate': startDate.strftime("%Y-%m-%d %H:%M:%S"), 'endDate': endDate.strftime("%Y-%m-%d %H:%M:%S"), 'duration': (endDate - startDate + timedelta(days=1)).days})
            
            def breakDownTime(startDate, endDate):
                while startDate <= endDate:
                    nextWeek = startDate + timedelta(days=(6 - startDate.weekday()))
                    if nextWeek > endDate:
                        printWeekOrNot(startDate, endDate)
                        break
                    else:
                        printWeekOrNot(startDate, nextWeek)
                        startDate = nextWeek + timedelta(days=1)
            
            breakDownTime(startDate, endDate)
            return dates
        broken_durations = storeDates(startDate, endDate)

        # create timesheets with the broken dates
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for duration in broken_durations:
                if action == 'Save':
                    currentDate = datetime.now()
                    startDate = datetime.strptime(duration['startDate'], '%Y-%m-%d %H:%M:%S')
                    if (startDate-currentDate<=timedelta(1)):
                        status = "Active"
                    else:
                        status = "Upcoming"
                args = {'duration': duration, 'projectID': projectID, 'workDay': workDay, 'description': description, 'status': status, 'assignGroupID': assignGroupID, 'manager_id': manager_id}
                futures.append(executor.submit(store_timesheet_object, args))

        # wait for all futures to complete
        for future in futures:
            future.result()

        return make_response(jsonify(success_message), 200)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def edit_data(data,manager_id,client):
    try: 
        # Convert string to ObjectId
        projectID = ObjectId(data["projectID"])
        assignGroupID = ObjectId(data["assignGroupID"])
        managerSheetID = ObjectId(data["managerSheetID"])
        # Convert string to datetime
        startDate = datetime.strptime(data['startDate'], "%Y-%m-%d %H:%M:%S")
        endDate = datetime.strptime(data['endDate'], "%Y-%m-%d %H:%M:%S")

        # Extract other fields
        action = data["action"]
        # if action is not "Draft" or "Save", throw error with message: "Illegal Action for timesheet"
        if action not in ["Draft", "Save"]:
            return make_response(jsonify({"error": "Illegal Action for timesheet. Action must be 'Save' or 'Draft'"}), 400)

        # fetch the current status of sheet
        current_status = str(client.TimesheetDB.ManagerSheets.find_one({"_id": managerSheetID}, {"status": 1})['status'])
        status=""
        success_message=""
        if action == "Draft":
            status = "Draft"
            success_message = {"message": "Timesheet saved to Draft successfully"}
        elif action == "Save":
            success_message = {"message": "Timesheet assigned successfully"}
            if current_status == "Draft":
                currentDate = datetime.now()
                if (startDate-currentDate<timedelta(1)):
                    status = "Active"
                else:
                    status = "Upcoming"
            else:
                # return make_response(jsonify({"message": status}),200)
                # return make_response(jsonify
                status = current_status
        
        # Extract other fields
        description = data["description"]

        # Create WorkDay object
        workDay = {
            "mon": WorkDay(work=bool(data["workDay"]["mon"])),
            "tue": WorkDay(work=bool(data["workDay"]["tue"])),
            "wed": WorkDay(work=bool(data["workDay"]["wed"])),
            "thu": WorkDay(work=bool(data["workDay"]["thu"])),
            "fri": WorkDay(work=bool(data["workDay"]["fri"])),
            "sat": WorkDay(work=bool(data["workDay"]["sat"])),
            "sun": WorkDay(work=bool(data["workDay"]["sun"])),
        }
        # convert workDay to string dictionary
        workDay = {day: vars(workDay) for day, workDay in workDay.items()}
        # return make_response(jsonify({"message": str(workDay)}), 200)
        # Draft status can edit all the fields

        # store the current state of the ManagerSheet for comparison
        current_managerSheet = client.TimesheetDB.ManagerSheets.find_one({"_id": managerSheetID})
        # if status is Draft, then update all fields
        if current_status == "Draft":
            # update fields in database
            client.TimesheetDB.ManagerSheets.update_one({"_id": managerSheetID}, {"$set": {"projectID": projectID, "startDate": startDate, "endDate": endDate, "workDay": workDay, "description": description, "status": status, "assignGroupID": assignGroupID}})
        # Upcoming status can edit all fields except assignGroupID
        elif current_status == "Upcoming":
            # update fields in database
            client.TimesheetDB.ManagerSheets.update_one({"_id": managerSheetID}, {"$set": {"projectID": projectID, "startDate": startDate, "endDate": endDate, "workDay": workDay, "description": description, "status": status}})
        # Active status can only projectID, workDay, and description
        elif current_status == "Active":
            # update fields in database
            client.TimesheetDB.ManagerSheets.update_one({"_id": managerSheetID}, {"$set": {"projectID": projectID, "workDay": workDay, "description": description}})
        else:
            return make_response(jsonify({"error": "Illegal Action for timesheet"}), 400) 

        # store the updated state of the ManagerSheet for comparison
        updated_managerSheet = client.TimesheetDB.ManagerSheets.find_one({"_id": managerSheetID})
        
        # return make_response(jsonify({"message": {"status": updated_managerSheet['status'], "current_status": current_status}}),200)
        # compare current_managerSheet with updated sheet and check if anything is changed or not
        if (current_managerSheet['projectID'] == updated_managerSheet['projectID'] 
            and current_managerSheet['startDate'] == updated_managerSheet['startDate'] 
            and current_managerSheet['endDate'] == updated_managerSheet['endDate']
            and current_managerSheet['workDay'] == updated_managerSheet['workDay']
            and current_managerSheet['description'] == updated_managerSheet['description']
            and current_managerSheet['status'] == updated_managerSheet['status']
            and current_managerSheet['assignGroupID'] == updated_managerSheet['assignGroupID']):
            # if not changed, return message "No changes made"
            return make_response(jsonify({"message": "No changes made"}), 200)

        lastUpdateDate = datetime.now()

        # Update the managerSheetsObjects field in TimesheetRecords Collection, if managerID is not matched create new entry
        existing_version = client.TimesheetDB.TimesheetRecords.find_one({"managerID": ObjectId(manager_id)}, {"managerSheetsInstances": {"$elemMatch": {"managerSheetsObjects": ObjectId(managerSheetID)}}})
        updated_version = existing_version['managerSheetsInstances'][0]['version'] + 1
        # update the last update date and version of the entry in TimesheetRecords Collection
        client.TimesheetDB.TimesheetRecords.update_one(
                                                        {"managerID": ObjectId(manager_id), "managerSheetsInstances.managerSheetsObjects": ObjectId(managerSheetID)},
                                                        {"$set": {"managerSheetsInstances.$.lastUpdateDate": lastUpdateDate, "managerSheetsInstances.$.version": updated_version}}
                                                    )

        return make_response(jsonify({"message": success_message}), 200)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def return_timesheet(manager_uuid, timesheet):
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

                # check if managerSheetID is valid
                if timesheet['managerSheetID'] is not None:
                    timesheet['managerSheetID'] = ObjectId(timesheet['managerSheetID'])
                    verify = verify_attribute(collection=client.TimesheetDB.ManagerSheets, key="_id",attr_value=timesheet['managerSheetID'])
                    if not verify:
                        return make_response(jsonify({"error": "timesheet 'managerSheetID' data is incorrect"}), 400)    
                else:
                    return make_response(jsonify({"error": "timesheet 'managerSheetID' data is required"}), 400)
                
                # check if employeeSheetID is valid
                if timesheet['employeeSheetID'] is not None:
                    timesheet['employeeSheetID'] = ObjectId(timesheet['employeeSheetID'])
                    verify = verify_attribute(collection=client.TimesheetDB.ManagerSheets, key="_id",attr_value=timesheet['employeeSheetID'])
                    if not verify:
                        return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is incorrect"}), 400)    
                else:
                    return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is required"}), 400)

                # check if return_message is valid
                if timesheet['returnMessage'] is not None:
                    timesheet['returnMessage'] = str(timesheet['returnMessage'])
                else:
                    return make_response(jsonify({"error": "'return message' data is required"}), 400)
            else:
                return make_response(jsonify({"error": "timesheet data is required"}), 400)
            
            # update the returnMessage field in the employeeSheetInstances field in EmployeeSheets Collection
            client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet['employeeSheetID']},
                                                         {"$set": {"returnMessage": timesheet['returnMessage'], "status": "Returned"}})

            # return make_response(jsonify({"message": "Working"}), 200)
            # Return the new timesheet as a JSON response
            return make_response(jsonify({"message": str("Timesheet Returned Successfully")}), 200)    

        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
              
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def approve_timesheet(manager_uuid, timesheet):
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

                # check if managerSheetID is valid
                if timesheet['managerSheetID'] is not None:
                    verify = verify_attribute(collection=client.TimesheetDB.ManagerSheets, key="_id",attr_value=ObjectId(timesheet['managerSheetID']))
                    if not verify:
                        return make_response(jsonify({"error": "timesheet 'managerSheetID' data is incorrect"}), 400)    
                    verify = verify_attribute(collection=client.TimesheetDB.ManagerSheets, key="employeeSheetID",attr_value=ObjectId(timesheet['employeeSheetID']))
                    if not verify:
                        return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is incorrect"}), 400)
                else:
                    return make_response(jsonify({"error": "timesheet 'managerSheetID' data is required"}), 400)
                
                # check if employeeSheetID is valid
                if timesheet['employeeSheetID'] is not None:
                    verify = verify_attribute(collection=client.TimesheetDB.EmployeeSheets, key="_id",attr_value=ObjectId(timesheet['employeeSheetID']))
                    if not verify:
                        return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is incorrect"}), 400)    
                else:
                    return make_response(jsonify({"error": "timesheet 'employeeSheetID' data is required"}), 400)

            else:
                return make_response(jsonify({"error": "timesheet data is required"}), 400)
            
            # update the returnMessage field in the employeeSheetInstances field in EmployeeSheets Collection
            response = client.TimesheetDB.ManagerSheets.update_one({"_id": ObjectId(timesheet['managerSheetID'])},
                                                         {"$set": {"status": "Submitted"}})
            if not response.modified_count:
                return make_response(jsonify({"error": "Failed to update the timesheet"}), 500)
            response = client.TimesheetDB.EmployeeSheets.update_one({"_id": ObjectId(timesheet['employeeSheetID'])},
                                                         {"$set": {"status": "Submitted"}},)
            if not response.modified_count:
                return make_response(jsonify({"error": "Failed to update the timesheet"}), 500)
            # if employeeSheet contains returnMessage field, remove the whole field totally
            response = client.TimesheetDB.EmployeeSheets.update_one({"_id": ObjectId(timesheet['employeeSheetID'])},
                                                         {"$unset": {"returnMessage": ""}})
            # return make_response(jsonify(timesheet), 200)
            # Return the new timesheet as a JSON response
            return make_response(jsonify({"message": str("Timesheet Approved")}), 200)    

        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
              
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def edit_timesheet(manager_uuid, timesheet):
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

                # check if timesheetRecords is valid
                if timesheet['managerSheetID'] is not None:
                    timesheet['managerSheetID'] = ObjectId(timesheet['managerSheetID'])
                    verify = verify_attribute(collection=client.TimesheetDB.ManagerSheets, key="_id",attr_value=timesheet['managerSheetID'])
                    if not verify:
                        return make_response(jsonify({"error": "timesheet 'managerSheetID' data is incorrect"}), 400)
                    # check if TImesheetRecords has a document where for a specific manager_id, there exists a managerSheetID at managerSheetObject in managerSheetsInstances
                    verify = client.TimesheetDB.TimesheetRecords.find_one({'managerID': ObjectId(manager_id), 'managerSheetsInstances.managerSheetsObjects': ObjectId(timesheet['managerSheetID'])})
                    if not verify:
                      return make_response(jsonify({"error": "manager doesnt has access to this timesheet"}), 400)
                        
                else:
                    return make_response(jsonify({"error": "timesheet 'managerSheetID' data is required"}), 400)

                # check if the timesheet status allows upgradation of status updates
                timesheets = client.TimesheetDB.ManagerSheets.find_one({"_id": ObjectId(timesheet['managerSheetID'])})
                if not timesheets:
                    return make_response(jsonify({"error": "No timesheet found to edit"}), 400)
                # only draft and upcoming can be edited to update the status
                if timesheets['status'] == "Active" and timesheet['action'] == "Draft":
                    return make_response(jsonify({"error": "Timesheet is Active, status can not be changed"}), 400)
                elif timesheets['status'] == "Submitted":
                    return make_response(jsonify({"error": "Timesheet is Submitted, status can not be changed"}), 400)
                elif timesheets['status'] == "Review":
                    return make_response(jsonify({"error": "Timesheet is in Review, status can not be changed"}), 400)
                
                # check if action is valid
                if timesheet['action'] is not None:
                    # action must be 'Save' or 'Draft'
                    if timesheet['action'] not in ["Save", "Draft"]:
                        return make_response(jsonify({"error": "Illegal Action for timesheet. Action must be 'Save' or 'Draft'"}), 400)
                else:
                    return make_response(jsonify({"error": "'action' data is required"}), 400)

                # check if assignGroupID is valid
                if timesheet['assignGroupID'] is not None:
                    timesheet['assignGroupID'] = ObjectId(timesheet['assignGroupID'])
                    verify = verify_attribute(collection=client.TimesheetDB.AssignmentGroup, key="_id",attr_value=timesheet['assignGroupID'])
                    if not verify.status_code == 200:
                        # If the connection fails, return the error response
                        return verify
                else:
                    return make_response(jsonify({"error": "timesheet 'assignGroupID' data is required"}), 400)
                
                # check if projectID is valid
                if 'projectID' in timesheet:
                    timesheet['projectID'] = ObjectId(timesheet['projectID'])
                    verify = verify_attribute(collection=client.WorkBaseDB.Projects, key="_id",attr_value=timesheet['projectID'])
                    if not verify.status_code == 200:
                        # If the connection fails, return the error response
                        return verify
                else:
                    return make_response(jsonify({"error": "timesheet 'projectID' data is required"}), 400)
                    
                # check if startDate is greater than endDate format:2024-02-05 18:30:00
                if 'startDate' in timesheet and 'endDate' in timesheet:
                    start = datetime.strptime(timesheet['startDate'], "%Y-%m-%d %H:%M:%S")
                    end = datetime.strptime(timesheet['endDate'], "%Y-%m-%d %H:%M:%S")
                    # fetch current sheet startDate and endDate from database
                    current_sheet = client.TimesheetDB.ManagerSheets.find_one({"_id": ObjectId(timesheet['managerSheetID'])}, {"startDate": 1, "endDate": 1, "status": 1})
                    if not current_sheet:
                        return make_response(jsonify({"error": "No timesheet found to edit"}), 400)
                    # if status is Active, then the startDate and endDate can not be changed
                    if current_sheet['status'] == "Active":
                        if start != current_sheet['startDate'] or end != current_sheet['endDate']:
                            return make_response(jsonify({"error": "Timesheet is Active, start and end date can not be changed"}), 400)
                    
                    curr = datetime.now()
                    if current_sheet['status'] == "Draft" or current_sheet['status'] == "Upcoming":
                        if (start >= end) or (start<curr) or (end<=curr):
                            return make_response(jsonify({"error": "timesheet duration data is incorrect, update the start/end date"}), 400)
                else:
                    return make_response(jsonify({"error": "timesheet duration data is required"}), 400)

            else:
                return make_response(jsonify({"error": "timesheet data is required"}), 400)
            
            editManagerSheetResponse=edit_data(timesheet,manager_id,client)
            
            if not editManagerSheetResponse.status_code == 200:
                # If the connection fails, return the error response
                return editManagerSheetResponse
            # Return the new timesheet as a JSON response
            return make_response(jsonify({"message": str(editManagerSheetResponse.json['message'])}), 200)    

        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def delete_timesheet(manager_uuid, timesheet):
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

                # check if timesheetRecords is valid
                if timesheet['managerSheetID'] is not None:
                    timesheet['managerSheetID'] = ObjectId(timesheet['managerSheetID'])
                    verify = verify_attribute(collection=client.TimesheetDB.ManagerSheets, key="_id",attr_value=timesheet['managerSheetID'])
                    if not verify:
                        return make_response(jsonify({"error": "'managerSheetID' data is incorrect"}), 400)
                    # check if TImesheetRecords has a document where for a specific manager_id, there exists a managerSheetID at managerSheetObject in managerSheetsInstances
                    verify = client.TimesheetDB.TimesheetRecords.find_one({'managerID': ObjectId(manager_id), 'managerSheetsInstances.managerSheetsObjects': ObjectId(timesheet['managerSheetID'])})
                    if not verify:
                      return make_response(jsonify({"error": "Manager doesnt has access to this timesheet"}), 400)
                        
                else:
                    return make_response(jsonify({"error": "'managerSheetID' data is required"}), 400)

            else:
                return make_response(jsonify({"error": "Timesheet data is required"}), 400)

            timesheets = client.TimesheetDB.ManagerSheets.find_one({"_id": ObjectId(timesheet['managerSheetID'])})
            if not timesheets:
                return make_response(jsonify({"error": "No timesheet found to delete"}), 400)
            # only draft and upcoming can be deleted
            if timesheets['status'] == "Active":
                return make_response(jsonify({"error": "Timesheet is Active, cannot be deleted"}), 400)
            elif timesheets['status'] == "Submitted":
                return make_response(jsonify({"error": "Timesheet is Submitted, cannot be deleted"}), 400)
            elif timesheets['status'] == "Review":
                return make_response(jsonify({"error": "Timesheet is in Review, cannot be deleted"}), 400)
            
            # delete the managerSheet from the ManagerSheets Collection and the managerSheetsInstances from the TimesheetRecords Collection
            client.TimesheetDB.ManagerSheets.delete_one({"_id": timesheet['managerSheetID']})
            client.TimesheetDB.TimesheetRecords.update_one({"managerID": ObjectId(manager_id)}, {"$pull": {"managerSheetsInstances": {"managerSheetsObjects": timesheet['managerSheetID']}}})

            # Return the success message as a JSON response
            return make_response(jsonify({"message": "Timesheet Deletion Successful"}), 200)

        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
        
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

                # check if projectID is valid
                if 'projectID' in timesheet:
                    timesheet['projectID'] = ObjectId(timesheet['projectID'])
                    verify = verify_attribute(collection=client.WorkBaseDB.Projects, key="_id",attr_value=timesheet['projectID'])
                    if not verify.status_code == 200:
                        # If the connection fails, return the error response
                        return verify
                    # check if manager has access to this project
                    projects = client.WorkBaseDB.Projects.find_one({'_id': ObjectId(timesheet['projectID'])},{"_id": 1,"managerID": 1})
                    if str(manager_id) != str(projects['managerID']):
                        return make_response(jsonify({"error": "Manager doesnt has access to this project"}), 400)
                else:
                    return make_response(jsonify({"error": "Project is required to create Timesheet"}), 400)
                
                # check if assignGroupID is valid
                if 'assignGroupID' in timesheet:
                    timesheet['assignGroupID'] = ObjectId(timesheet['assignGroupID'])
                    verify = verify_attribute(collection=client.WorkBaseDB.AssignmentGroup, key="_id",attr_value=timesheet['assignGroupID'])
                    if not verify.status_code == 200:
                        # If the connection fails, return the error response
                        return verify
                else:
                    return make_response(jsonify({"error": "Assignee Group is required to create Timesheet"}), 400)

                # return make_response(jsonify({"success": True}), 200)
                # check if assignment group is part of project
                verify = verify_attribute(collection=client.WorkBasetDB.AssignmentGroup, key="projectID",attr_value=timesheet['projectID'])
                if not verify:
                    return make_response(jsonify({"error": "Assignee Group is not associated with the Project"}), 400)
                    
                # check if startDate is greater than endDate format:2024-02-05 18:30:00
                if 'startDate' in timesheet and 'endDate' in timesheet:
                    start = datetime.strptime(timesheet['startDate'], "%Y-%m-%d %H:%M:%S")
                    end = datetime.strptime(timesheet['endDate'], "%Y-%m-%d %H:%M:%S")
                    curr = datetime.now()
                    if (start >= end) or (start<curr) or (end<=curr):
                        return make_response(jsonify({"error": "Timesheet duration is incorrect"}), 400)
                else:
                    return make_response(jsonify({"error": "Timesheet start/end date is required"}), 400)

            else:
                return make_response(jsonify({"error": "Provide necessary details to create Timesheet"}), 400)


            
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

def get_workData(client, manager_id):
    """
    Retrieves all assignments, projects, tasks, and employees for a manager from the database.

    Args:
        client (MongoClient): An instance of MongoClient.
        manager_id (str): The ID of the manager.

    Returns:
        JSON response: A JSON response containing the manager data or an error message.
    """
    try: 
        # Use aggregation pipeline to match the employee ID and project the required fields
        project_pipeline = [
  {"$lookup": {"from": "Projects","localField": "_id","foreignField": "managerID","as": "Projects"}},
      {"$match": {"Projects": {"$ne": []}}},
  {"$lookup": {"from": "AssignmentGroup","localField": "Projects._id","foreignField": "projectID","as": "Assignee"}},
  {"$project": {
                "role": 0,
                "employeeDataID": 0,
                "name": 0,
                "Projects.managerID": 0,
                "Projects.status": 0,
                "Assignee.assignedBy": 0,
                "Assignee.assignmentInstances.assignDate": 0,
                }},
  {"$project": {
              "_id": 1,
                "Projects": 1,
                "Assignee": {"$map": {"input": "$Assignee",
                                              "as": "group",
                                              "in": {"_id": "$$group._id",
                                                     "name": "$$group.name",
                                                     "assignmentInstances": {
                                                         "$map": {"input": "$$group.assignmentInstances",
                                                         "as": "instance",
                                                         "in": "$$instance.assignmentID"}},
                                                      "projectID": "$$group.projectID"
                                                                  }}}}},
  {"$addFields": {
    "Projects": {
      "$map": {
        "input": "$Projects",
        "as": "project",
        "in": {
          "$mergeObjects": [
            "$$project",
            {
              "Assignee": {
                "$map": {
                  "input": {
                    "$filter": {
                      "input": "$Assignee",
                      "as": "group",
                      "cond": {"$eq": ["$$group.projectID", "$$project._id"]}
                    }
                  },
                  "as": "group",
                  "in": "$$group"
                }
              },
            }
          ]
        }
      }
    }
  }
},
{"$project": {"Projects.Assignee.assignmentInstances": 0,"Projects.Assignee.projectID": 0}},
{"$project": {"_id": 0,
              "managerID": "$_id",
              "Projects._id": 1,"Projects.name": 1,
              "Projects.Assignee._id": 1,"Projects.Assignee.name": 1}},
                {"$match": {"managerID": ObjectId(manager_id)}},
                {"$project": {"managerID": 0}}
                ]

        manager_data = list(client.WorkBaseDB.Members.aggregate(project_pipeline))

        # Check if manager data is empty
        if not manager_data:
            return make_response(jsonify({"message": "No Data here yet"}), 200)

        # Convert the employee_sheets cursor object to a JSON object
        manager_json = json.dumps(manager_data, default=str)
        manager_data_results = json.loads(manager_json)
        # Return the JSON response
        return make_response(jsonify({"managerProjectData": manager_data_results}), 200)
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def fetch_managerData(manager_uuid):
    """
    This function fetches the manager data for assignments, projects, tasks, employees used for timesheet assignments
    It takes a manager ID as input.
    It returns a JSON response containing the manager data or an error message.
    """
    try: 
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        if isinstance(client, MongoClient):
            # check if the userID is valid
            verify = get_WorkAccount(client, manager_uuid)
            if not verify.status_code == 200:
                # If the connection fails, return the error response
                return verify
            manager_id = verify.json['_id']
            # Call the get_timesheets_for_manager function with the manager ID
            managerData_response = get_workData(client, manager_id)  
            
            return managerData_response
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
            
    
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)