# Import necessary modules
from datetime import datetime
from bson import ObjectId
from flask import jsonify, make_response
from pymongo import MongoClient
import json

from ....connectors.dbConnector import dbConnectCheck, get_WorkAccount, verify_attribute

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
                                                "Status":  "$status",
                                                "ReturnedMessage": "$returnMessage"}}
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

        # sort the sheets by their startDate
        timesheets = sorted(timesheets, key=lambda x: x['Start Date'])

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
                            return make_response(jsonify({"error": "Cannot update a day's work more than one day after"}), 400)

                    # else, update the hour and comment for the latest instance of employeeSheetInstance at employeeSheetObject
                    [client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet['employeeSheetID'], "employeeSheetInstances": {"$elemMatch": {"version": current_sheet['employeeSheetInstances'][-1]["version"]}}}, {"$set": {"employeeSheetInstances.$.employeeSheetObject.workDay."+day: timesheet['workDay'][day]}}) for day in days_of_week]
        
                elif current_sheet['status'] == "Returned":
                    # get list of workdays which were updated
                    updated_days = [day for day in timesheet["workDay"] if timesheet["workDay"][day]['hour'] != current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]['hour']]
                    updated_overall_days = [day for day in timesheet["workDay"] if timesheet["workDay"][day] != current_sheet['employeeSheetInstances'][len(current_sheet['employeeSheetInstances'])-1]['employeeSheetObject']['workDay'][day]]
                    if len(updated_overall_days) == 0:
                        return make_response(jsonify({"error": "No workDay details updated"}), 400)

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
                    return make_response(jsonify({"error": "timesheet 'status' data is incorrect"}), 400)
                
                # after successful action, return message Day's work update successful
                return make_response(jsonify({"message": "Day's work update successful"}), 200)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)