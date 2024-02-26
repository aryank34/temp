from datetime import datetime
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
client = MongoClient('mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority&appName=EmployeePortal', server_api=ServerApi('1'), UuidRepresentation="standard")


class ManagerSheetsInstance:
    def __init__(self, lastUpdateDate: datetime, managerSheetsObjectID: ObjectId, version: int = 0):
        self.managerSheetsObjects = managerSheetsObjectID
        self.lastUpdateDate = lastUpdateDate
        self.version = version
    
    def to_dict(self):
        return {
            "managerSheetsObjects": self.managerSheetsObjects,
            "lastUpdateDate": self.lastUpdateDate,
            "version": self.version
        }

class TimesheetRecord:
    def __init__(self, managerID: ObjectId, managerSheetsInstances: list[ManagerSheetsInstance]):
        self.managerID = managerID
        self.managerSheetsInstances = managerSheetsInstances

    def to_dict(self):
        return {
            "managerID": self.managerID,
            "managerSheetsInstances": [vars(managerSheetsInstance) for managerSheetsInstance in self.managerSheetsInstances]
        }

class WorkDay:
    def __init__(self, work: bool):
        self.work = work
        self.hour = int(0)
        self.comment = str("")

class ManagerSheetsAssign:
    def __init__(self, projectID: ObjectId, startDate: datetime, endDate: datetime, workDay: dict[str, WorkDay], description: str, status: str, assignGroupID: ObjectId):
        self.projectID = projectID
        self.startDate = startDate
        self.endDate = endDate
        self.workDay = workDay
        self.description = description
        self.status = status
        self.assignGroupID = assignGroupID
    
    def to_dict(self):
        return {
            "projectID": self.projectID,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "workDay": {day: vars(workDay) for day, workDay in self.workDay.items()},
            "description": self.description,
            "status": self.status,
            "assignGroupID": self.assignGroupID,
        }

class EmployeeSheetObject:
    def __init__(self, projectID: ObjectId, taskID: ObjectId, workDay: dict[str, WorkDay], description: str):
        self.projectID = projectID
        self.taskID = taskID
        self.workDay = workDay
        self.description = description
    def to_dict(self):
        return {
            "projectID": self.projectID,
            "taskID": self.taskID,
            "workDay": {day: vars(workDay) for day, workDay in self.workDay.items()},
            "description": self.description
        }

class EmployeeSheetInstance:
    def __init__(self, version: int, employeeSheetObject: EmployeeSheetObject):
        self.version = version
        self.employeeSheetObject = employeeSheetObject.to_dict()
    def to_dict(self):
        return {
            "version": self.version,
            "employeeSheetObject": self.employeeSheetObject
        }

class ManagerSheetReview:
    def __init__(self, status: str, employeeSheetID: ObjectId):
        self.employeeSheetID = employeeSheetID
        self.status = status
    def to_dict(self):
        return {
            "employeeSheetID": self.employeeSheetID,
            "status": self.status
        }

class EmployeeSheet:
    def __init__(self, managerSheetID: ObjectId, employeeID: ObjectId, managerID: ObjectId, startDate: datetime, endDate: datetime, employeeSheetInstances: list[EmployeeSheetInstance]):
        self.managerSheetID = managerSheetID
        self.employeeID = employeeID
        self.managerID = managerID
        self.startDate = startDate
        self.endDate = endDate
        self.employeeSheetInstances = employeeSheetInstances
        self.status = "Ongoing"
    def to_dict(self):
        return {
            "managerSheetID": self.managerSheetID,
            "employeeID": self.employeeID,
            "managerID": self.managerID,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "employeeSheetInstances": [vars(employeeSheetInstance) for employeeSheetInstance in self.employeeSheetInstances],
            "status": self.status
        } 

class AssignmentInstance:
    def __init__(self, assignDate: datetime, assignmentID: ObjectId):
        self.assignDate = assignDate
        self.assignmentID = assignmentID

class AssignmentGroup:
    def __init__(self, name: str, assignmentInstances: list[AssignmentInstance]):
        self.name = name
        self.assignmentInstances = assignmentInstances


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
            msg_str = "Employee Sheet Created"+": EmployeeSheetID :"+ str(result.inserted_id)
        else:
            if (client.TimesheetDB.EmployeeSheets.find_one({"managerSheetID": employeeSheet.managerSheetID, "employeeID": employeeSheet.employeeID, "employeeSheetInstances": {"$elemMatch": {"version": version}}}) is None):
                result = client.TimesheetDB.EmployeeSheets.update_one({"employeeID": employeeSheet.employeeID, "managerSheetID": employeeSheet.managerSheetID},
                                                            {"$push": {"employeeSheetInstances": employeeSheetInstance.to_dict()}})
                msg_str = "Employee Sheet updated"
            
            else:
                msg_str = "Employee Sheet already exists"

        print(msg_str)


    except Exception as e:
        # If an error occurs, return the error response
        print("Error creating Timesheet Records: ", e)


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

if len(timesheet_documents) == 0:
    print("No Timesheet Records found")
    exit()
if len(timesheet_documents) == 0:
    print("No Assignment Records found")
    exit()

# Convert MongoDB query results to DataFrames
timesheet_df = pd.DataFrame(timesheet_documents)
assignment_df = pd.DataFrame(assignment_documents)
result_df = pd.merge(timesheet_df, assignment_df, on='assignmentID', how='inner')
result_documents = result_df.to_dict(orient='records')
for i in range(len(result_documents)):
    subset_dict = {key: result_documents[i][key] for key in ['managerSheetID', 'startDate', 'endDate', 'status', 'version', 'workDay', 'description', 'Project', 'Task', 'Employee', 'Manager'] if key in result_documents[i]}
    # doc_res.append(subset_dict)
    store_employee_sheets(subset_dict, client)
