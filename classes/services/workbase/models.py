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
    def to_dict(self):
        return {
            "name": self.name,
            "projectID": self.projectID,
            "leadID": self.leadID
        }

class Job:
    def __init__(self, jobID: int, job: str, deadline: datetime, activeStatus: bool):
        self.jobID = jobID
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
    def to_dict(self):
        return {
            "name": self.name,
            "projectID": self.projectID,
            "billable": self.billable,
            "deadline": self.deadline,
            "joblist": self.joblist,
            "description": self.description,
            "completionStatus": self.completionStatus
        }


class Project:
    def __init__(self, name: str, description: str, managerID: ObjectId, status: str, budget: float, actual_cost: float, planned_cost: float, created_at: datetime, created_by: ObjectId):
        self.name = name
        self.description = description
        self.managerID = managerID
        self.status = status
        self.budget = budget
        self.actual_cost = actual_cost
        self.planned_cost = planned_cost
        self.created_at = created_at
        self.created_by = created_by
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "managerID": self.managerID,
            "status": self.status,
            "budget": self.budget,
            "actual_cost": self.actual_cost,
            "planned_cost": self.planned_cost,
            "created_at": self.created_at,
            "created_by": self.created_by
        }

class Member:
    def __init__(self, name: str, teamID: ObjectId, role: str, employeeDataID: ObjectId):
        self.name = name
        self.teamID = teamID
        self.role = role
        self.employeeDataID = employeeDataID

class Assignment:
    def __init__(self, assignedBy: str, name: str, projectID: ObjectId, taskID: ObjectId, assignedTo: list[ObjectId]):
        self.assignedBy = assignedBy
        self.name = name
        self.projectID = projectID
        self.taskID = taskID
        self.assignedTo = assignedTo
    def to_dict(self):
        return {
            "assignedBy": self.assignedBy,
            "name": self.name,
            "projectID": self.projectID,
            "taskID": self.taskID,
            "assignedTo": self.assignedTo
        }

