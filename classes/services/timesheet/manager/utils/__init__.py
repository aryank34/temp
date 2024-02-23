# Import necessary modules
from datetime import datetime, timedelta
from bson import ObjectId
from flask import Flask, jsonify, make_response
from pymongo import MongoClient
import os
from dotenv import load_dotenv, find_dotenv
import json
from ...models import ManagerSheetsAssign,ManagerSheetsInstance,WorkDay
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
                              "submittedSheets": "$employeeSheets.employeeSheetInstances"
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
                    project_id = filtered_timesheets[i]['submittedSheets'][j]['employeeSheetObject'].pop('projectID', None)
                    if project_id is not None:
                        project_item = project_dict.get(project_id)
                        if project_item:
                            filtered_timesheets[i]['submittedSheets'][j]['employeeSheetObject']['Project'] = project_item
                    task_id = filtered_timesheets[i]['submittedSheets'][j]['employeeSheetObject'].pop('taskID', None)
                    if task_id is not None:
                        task_item = task_dict.get(task_id)
                        if task_item:
                            filtered_timesheets[i]['submittedSheets'][j]['employeeSheetObject']['Task'] = task_item

        # Check if Timesheet list is empty
        if not filtered_timesheets:
            return make_response(jsonify({"message": "No Timesheets here yet"}), 200)

        # return make_response(jsonify({"message": "Working in review"}), 200)
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
        status = current_managerSheet['status']
        if status == "Draft":
            # update fields in database
            client.TimesheetDB.ManagerSheets.update_one({"_id": managerSheetID}, {"$set": {"projectID": projectID, "startDate": startDate, "endDate": endDate, "workDay": workDay, "description": description, "status": status, "assignGroupID": assignGroupID}})
        # Upcoming status can edit all fields except assignGroupID
        elif status == "Upcoming":
            # update fields in database
            client.TimesheetDB.ManagerSheets.update_one({"_id": managerSheetID}, {"$set": {"projectID": projectID, "startDate": startDate, "endDate": endDate, "workDay": workDay, "description": description, "status": status}})
        # Active status can only projectID, workDay, and description
        elif status == "Active":
            # update fields in database
            client.TimesheetDB.ManagerSheets.update_one({"_id": managerSheetID}, {"$set": {"projectID": projectID, "workDay": workDay, "description": description}})
        else:
            return make_response(jsonify({"error": "Illegal Action for timesheet"}), 400) 

        # store the updated state of the ManagerSheet for comparison
        updated_managerSheet = client.TimesheetDB.ManagerSheets.find_one({"_id": managerSheetID})
        
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

        return make_response(jsonify({"message": "Timesheet Edit Successful"}), 200)
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

            return make_response(jsonify({"message": "Working"}), 200)
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

            else:
                return make_response(jsonify({"error": "timesheet data is required"}), 400)
            
            # update the returnMessage field in the employeeSheetInstances field in EmployeeSheets Collection
            client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet['employeeSheetID']},
                                                         {"$set": {"status": "Submitted"}})
            client.TimesheetDB.ManagerSheets.update_one({"_id": timesheet['managerSheetID']},
                                                         {"$set": {"status": "Submitted"}})
            # if employeeSheet contains returnMessage field, remove the whole field totally
            client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet['employeeSheetID']},
                                                         {"$unset": {"returnMessage": ""}})

            # return make_response(jsonify({"message": "Working"}), 200)
            # Return the new timesheet as a JSON response
            return make_response(jsonify({"message": str("Timesheet Returned Successfully")}), 200)    

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
                    curr = datetime.now()
                    if (start >= end) or (start<=curr) or (end<=curr):
                        return make_response(jsonify({"error": "timesheet duration data is incorrect"}), 400)
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
                        return make_response(jsonify({"error": "timesheet 'managerSheetID' data is incorrect"}), 400)
                    # check if TImesheetRecords has a document where for a specific manager_id, there exists a managerSheetID at managerSheetObject in managerSheetsInstances
                    verify = client.TimesheetDB.TimesheetRecords.find_one({'managerID': ObjectId(manager_id), 'managerSheetsInstances.managerSheetsObjects': ObjectId(timesheet['managerSheetID'])})
                    if not verify:
                      return make_response(jsonify({"error": "manager doesnt has access to this timesheet"}), 400)
                        
                else:
                    return make_response(jsonify({"error": "timesheet 'managerSheetID' data is required"}), 400)

            else:
                return make_response(jsonify({"error": "timesheet data is required"}), 400)

            timesheets = client.TimesheetDB.ManagerSheets.find_one({"_id": ObjectId(timesheet['managerSheetID'])})
            if not timesheets:
                return make_response(jsonify({"error": "No timesheet found"}), 400)
            # only draft and upcoming can be deleted
            if timesheets['status'] == "Active":
                return make_response(jsonify({"error": "timesheet is active, cannot be deleted"}), 400)
            elif timesheets['status'] == "Submitted":
                return make_response(jsonify({"error": "timesheet is submitted, cannot be deleted"}), 400)
            elif timesheets['status'] == "Review":
                return make_response(jsonify({"error": "timesheet is in review, cannot be deleted"}), 400)
            
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
          { "$group": {
              "_id": "$managerID",
              "Projects": {
                "$push": {
                  "projectID": "$_id",
                  "name": "$name"
                }
              }
            }
          },
          {
            "$project": {
              "_id": 0,
              "managerID": "$_id",
              "Projects": 1
            }
          },
          {"$match": {"managerID": ObjectId(manager_id)}},
        ]

        assignee_pipeline=[
          { "$group": {
              "_id": "$assignedBy",
              "Assignee": {
                "$push": {
                  "_id": "$_id",
                  "name": "$name"
                }
              }
            }
          },
          {
            "$project": {
              "_id": 0,
              "managerID": "$_id",
              "Assignee": 1
            }
          },
          {"$match": {"managerID": ObjectId(manager_id)}},
        ]

        manager_data = list(client.WorkBaseDB.Projects.aggregate(project_pipeline))
        assignee_data = list(client.TimesheetDB.AssignmentGroup.aggregate(assignee_pipeline))
        # Check if manager data is empty
        if not manager_data:
            return make_response(jsonify({"message": "No Data here yet"}), 200)
        # if not assignee_data:
        #     return make_response(jsonify({"message": "No Data here yet"}), 200)
        # Merge the manager data and assignee data on managerID
        for i in range(len(manager_data)):
            for j in range(len(assignee_data)):
                if manager_data[i]['managerID'] == assignee_data[j]['managerID']:
                    manager_data[i]['Assignee'] = assignee_data[j]['Assignee']
                    # pop managerID field
                    manager_data[i].pop('managerID')

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