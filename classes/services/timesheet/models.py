# Import necessary modules from flask_mongoengine and mongoengine
# from flask_mongoengine import MongoEngine
# from mongoengine import Document, EmbeddedDocument, StringField, BooleanField, IntField, DictField, EmbeddedDocumentField, DateTimeField, ObjectIdField, ListField

# Create an instance of MongoEngine
# db = MongoEngine()

from datetime import datetime
from bson.objectid import ObjectId

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
    def __init__(self, work: bool, hour: int = int(0), comment: str = str("")):
        self.work = work
        self.hour = hour
        self.comment = comment

    def to_dict(self):
        return {
            "work": self.work,
            "hour": self.hour,
            "comment": self.comment
        }

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
    def __init__(self, projectID: ObjectId, taskID: ObjectId, workDay: dict[str, WorkDay], description: str = str(""), billable: bool = False):
        self.projectID = projectID
        self.taskID = taskID
        self.workDay = {day: WorkDay(**workDay) if isinstance(workDay, dict) else workDay for day, workDay in workDay.items()}
        self.description = description
        self.billable = billable

    def to_dict(self):
        return {
            "projectID": self.projectID,
            "taskID": self.taskID,
            "workDay": {day: workDay.to_dict() for day, workDay in self.workDay.items()},
            "description": self.description,
            "billable": self.billable
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
    def __init__(self, employeeID: ObjectId, managerID: ObjectId, startDate: datetime, endDate: datetime, employeeSheetObject: list[EmployeeSheetObject], status: str='Ongoing'):
        self.employeeID = employeeID
        self.managerID = managerID
        self.startDate = startDate
        self.endDate = endDate
        self.employeeSheetObject = employeeSheetObject
        self.status = status

    def to_dict(self):
        return {
            "employeeID": self.employeeID,
            "managerID": self.managerID,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "employeeSheetObject": [obj.to_dict() for obj in self.employeeSheetObject],
            "status": self.status
        }

class AssignmentInstance:
    def __init__(self, assignDate: datetime, assignmentID: ObjectId):
        self.assignDate = assignDate
        self.assignmentID = assignmentID

class AssignmentGroup:
    def __init__(self, name: str, assignedBy: ObjectId, projectID: ObjectId, assignmentInstances: list[AssignmentInstance]):
        self.name = name
        self.assignedBy = assignedBy
        self.projectID = projectID
        self.assignmentInstances = assignmentInstances
    def to_dict(self):
        return {
            "name": self.name,
            "assignedBy": self.assignedBy,
            "projectID": self.projectID,
            "assignmentInstances": [vars(assignmentInstance) for assignmentInstance in self.assignmentInstances]
        }