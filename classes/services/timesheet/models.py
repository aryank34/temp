# Import necessary modules from flask_mongoengine and mongoengine
# from flask_mongoengine import MongoEngine
# from mongoengine import Document, EmbeddedDocument, StringField, BooleanField, IntField, DictField, EmbeddedDocumentField, DateTimeField, ObjectIdField, ListField

# Create an instance of MongoEngine
# db = MongoEngine()

from datetime import datetime
from bson.objectid import ObjectId

class ManagerSheetsInstance:
    def __init__(self, lastUpdateDate: datetime, managerSheetsObjectID: ObjectId):
        self.managerSheetsObjects = managerSheetsObjectID
        self.lastUpdateDate = lastUpdateDate
        self.version = int(0)
    
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
    def __init__(self, status: str, employeeSheetID: ObjectId, employeeID: ObjectId, startDate: datetime, endDate: datetime, employeeSheetInstances: list[EmployeeSheetInstance]):
        self.startDate = startDate
        self.endDate = endDate
        self.employeeSheetID = employeeSheetID
        self.employeeSheetInstances = employeeSheetInstances
        self.status = status
        self.employeeID = employeeID

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
