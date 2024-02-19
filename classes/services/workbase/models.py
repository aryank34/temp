# Import necessary modules from flask_mongoengine and mongoengine
# from flask_mongoengine import MongoEngine
# from mongoengine import Document, EmbeddedDocument, StringField, ObjectIdField, BooleanField, DateTimeField, ListField, EmbeddedDocumentField

# Create an instance of MongoEngine
# db = MongoEngine()

from datetime import datetime
from bson.objectid import ObjectId

class Team:
    def __init__(self, name: str, projectID: ObjectId, leadID: ObjectId):
        self.name = name
        self.projectID = projectID
        self.leadID = leadID

class Job:
    def __init__(self, job: str, deadline: datetime, activeStatus: bool):
        self.job = job
        self.deadline = deadline
        self.activeStatus = activeStatus


class Task:
    def __init__(self, name: str, projectID: ObjectId, billable: bool, deadline: datetime, joblist: list[Job], description: str, completionStatus: bool):
        self.name = name
        self.projectID = projectID
        self.billable = billable
        self.deadline = deadline
        self.joblist = joblist
        self.description = description
        self.completionStatus = completionStatus

class Project:
    def __init__(self, name: str, managerID: ObjectId, status: str):
        self.name = name
        self.managerID = managerID
        self.status = status

class Member:
    def __init__(self, name: str, teamID: ObjectId, role: str, employeeDataID: ObjectId):
        self.name = name
        self.teamID = teamID
        self.role = role
        self.employeeDataID = employeeDataID

class Assignment:
    def __init__(self, assignedBy: str, name: str, taskID: ObjectId, assignedTo: list[ObjectId]):
        self.assignedBy = assignedBy
        self.name = name
        self.taskID = taskID
        self.assignedTo = assignedTo

