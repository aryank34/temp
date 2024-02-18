# Import necessary modules from flask_mongoengine and mongoengine
# from flask_mongoengine import MongoEngine
# from mongoengine import Document, EmbeddedDocument, StringField, BooleanField, IntField, DictField, EmbeddedDocumentField, DateTimeField, ObjectIdField, ListField

# Create an instance of MongoEngine
# db = MongoEngine()

from datetime import datetime
from bson.objectid import ObjectId

class ManagerSheetsInstance:
    def __init__(self, lastUpdateDate: datetime, managerSheetsObjectID: ObjectId):
        self.lastUpdateDate = lastUpdateDate
        self.managerSheetsObjects = managerSheetsObjectID
    
    def to_dict(self):
        return {
            "lastUpdateDate": self.lastUpdateDate,
            "managerSheetsObjects": self.managerSheetsObjects
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
    def __init__(self, work: bool, hour: int, comment: str):
        self.work = work
        self.hour = hour
        self.comment = comment

class ManagerSheetsAssign:
    def __init__(self, projectID: ObjectId, startDate: datetime, endDate: datetime, workDay: dict[str, WorkDay], description: str, status: str, assignGroupID: ObjectId, sheetUpdate: bool):
        self.projectID = projectID
        self.startDate = startDate
        self.endDate = endDate
        self.workDay = workDay
        self.description = description
        self.status = status
        self.assignGroupID = assignGroupID
        self.sheetUpdate = sheetUpdate
    
    def to_dict(self):
        return {
            "projectID": self.projectID,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "workDay": {day: vars(workDay) for day, workDay in self.workDay.items()},
            "description": self.description,
            "status": self.status,
            "assignGroupID": self.assignGroupID,
            "sheetUpdate": self.sheetUpdate
        }

class EmployeeSheetObject:
    def __init__(self, projectID: ObjectId, taskID: ObjectId, workDay: dict[str, WorkDay], description: str):
        self.projectID = projectID
        self.taskID = taskID
        self.workDay = workDay
        self.description = description

class EmployeeSheetInstance:
    def __init__(self, version: int, employeeSheetObject: EmployeeSheetObject):
        self.version = version
        self.employeeSheetObject = employeeSheetObject

class ManagerSheetReview:
    def __init__(self, status: str, employeeSheetID: ObjectId, employeeID: ObjectId, startDate: datetime, endDate: datetime, employeeSheetInstances: list[EmployeeSheetInstance]):
        self.startDate = startDate
        self.endDate = endDate
        self.employeeSheetID = employeeSheetID
        self.employeeSheetInstances = employeeSheetInstances
        self.status = status
        self.employeeID = employeeID

class EmployeeSheet:
    def __init__(self, managerSheetID: ObjectId, employeeID: ObjectId, managerID: ObjectId, startDate: datetime, endDate: datetime, employeeSheetInstances: list[EmployeeSheetInstance], status: str):
        self.managerSheetID = managerSheetID
        self.employeeID = employeeID
        self.managerID = managerID
        self.startDate = startDate
        self.endDate = endDate
        self.employeeSheetInstances = employeeSheetInstances
        self.status = status
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







# # Define the TimeSheet model
# class TimeSheet(Document):
#     # _id = ObjectIdField()  # Unique ID of the timesheet
#     managerID = ObjectIdField()  # ID of the manager who created the timesheet
#     createdDate = DateTimeField()  # Date when the timesheet was created
#     managerSheetsObjects = ListField(ObjectIdField())  # List of IDs of the manager sheets in the timesheet

# # Define the Day model
# class Day(EmbeddedDocument):
#     work = BooleanField(required=True)  # Whether work was assigned for this day
#     hour = IntField(required=True)  # Number of hours worked on this day
#     comment = StringField()  # Comment for this day

# # Define the EmployeeSheetObject model
# class EmployeeSheetObject(EmbeddedDocument):
#     managerID = ObjectIdField()  # ID of the manager who assigned the task
#     projectID = ObjectIdField()  # ID of the project to which the task belongs
#     taskID = ObjectIdField()  # ID of the task
#     startDate = DateTimeField()  # Start date of the task
#     endDate = DateTimeField()  # End date of the task
#     workDay = DictField()  # Dictionary of work days
#     workDay['mon'] = EmbeddedDocumentField(Day, required=True)  # Monday's work day details
#     workDay['tue'] = EmbeddedDocumentField(Day, required=True)  # Tuesday's work day details
#     workDay['wed'] = EmbeddedDocumentField(Day, required=True)  # Wednesday's work day details
#     workDay['thu'] = EmbeddedDocumentField(Day, required=True)  # Thursday's work day details
#     workDay['fri'] = EmbeddedDocumentField(Day, required=True)  # Friday's work day details
#     workDay['sat'] = EmbeddedDocumentField(Day, required=True)  # Saturday's work day details
#     workDay['sun'] = EmbeddedDocumentField(Day, required=True)  # Sunday's work day details
#     description = StringField()  # Description of the task

# # Define the EmployeeSheetInstance model
# class EmployeeSheetInstance(EmbeddedDocument):
#     version = IntField()  # Version of the employee sheet
#     employeeSheetObject = EmbeddedDocumentField(EmployeeSheetObject)  # Embedded employee sheet object

# # Define the EmployeeSheets model
# class EmployeeSheets(Document):
#     # _id = ObjectIdField()  # Unique ID of the employee sheets
#     managerSheetID = ObjectIdField()  # ID of the manager sheet to which the employee sheets belong
#     employeeSheetInstances = ListField(EmbeddedDocumentField(EmployeeSheetInstance))  # List of employee sheet instances

# # Define the ManagerSheets model
# class ManagerSheets(Document):
#     # _id = ObjectIdField()  # Unique ID of the manager sheets
#     projectID = ObjectIdField()  # ID of the project to which the manager sheets belong
#     startDate = DateTimeField()  # Start date of the manager sheets
#     endDate = DateTimeField()  # End date of the manager sheets
#     workDay = DictField()  # Dictionary of work days
#     workDay['mon'] = EmbeddedDocumentField(Day, required=True)  # Monday's work day details
#     workDay['tue'] = EmbeddedDocumentField(Day, required=True)  # Tuesday's work day details
#     workDay['wed'] = EmbeddedDocumentField(Day, required=True)  # Wednesday's work day details
#     workDay['thu'] = EmbeddedDocumentField(Day, required=True)  # Thursday's work day details
#     workDay['fri'] = EmbeddedDocumentField(Day, required=True)  # Friday's work day details
#     workDay['sat'] = EmbeddedDocumentField(Day, required=True)  # Saturday's work day details
#     workDay['sun'] = EmbeddedDocumentField(Day, required=True)  # Sunday's work day details
#     description = StringField()  # Description of the manager sheets
#     status = StringField()  # Status of the manager sheets
#     assignGroupID = ObjectIdField()  # ID of the group to which the manager sheets are assigned

# # Define the AssignmentInstance model
# class AssignmentInstance(EmbeddedDocument):
#     assignDate = DateTimeField()  # Date when the assignment was assigned
#     assignmentid = ObjectIdField()  # ID of the assignment

# # Define the AssignmentGroup model
# class AssignmentGroup(Document):
#     # _id = ObjectIdField()  # Unique ID of the assignment group
#     name = StringField()  # Name of the assignment group
#     assignmentInstances = ListField(EmbeddedDocumentField(AssignmentInstance))  # List of assignment instances