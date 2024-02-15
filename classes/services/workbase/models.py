# Import necessary modules from flask_mongoengine and mongoengine
# from flask_mongoengine import MongoEngine
# from mongoengine import Document, EmbeddedDocument, StringField, ObjectIdField, BooleanField, DateTimeField, ListField, EmbeddedDocumentField

# Create an instance of MongoEngine
# db = MongoEngine()

from datetime import datetime
from bson.objectid import ObjectId

class Team:
    def __init__(self, _id: ObjectId, name: str, project_id: ObjectId, lead_id: ObjectId):
        self._id = _id
        self.name = name
        self.project_id = project_id
        self.lead_id = lead_id

class Job:
    def __init__(self, job: str, deadline: datetime, status: bool):
        self.job = job
        self.deadline = deadline
        self.status = status

class Task:
    def __init__(self, _id: ObjectId, name: str, project_id: ObjectId, billable: bool, deadline: datetime, joblist: list[Job], description: str, status: bool):
        self._id = _id
        self.name = name
        self.project_id = project_id
        self.billable = billable
        self.deadline = deadline
        self.joblist = joblist
        self.description = description
        self.status = status

class Project:
    def __init__(self, _id: ObjectId, name: str, manager_id: ObjectId, status: str):
        self._id = _id
        self.name = name
        self.manager_id = manager_id
        self.status = status

class Member:
    def __init__(self, _id: ObjectId, name: str, team_id: ObjectId, role: str, employee_data_id: ObjectId):
        self._id = _id
        self.name = name
        self.team_id = team_id
        self.role = role
        self.employee_data_id = employee_data_id

class Assignment:
    def __init__(self, _id: ObjectId, assigned_by: str, name: str, task_id: ObjectId, assigned_to: list[ObjectId]):
        self._id = _id
        self.assigned_by = assigned_by
        self.name = name
        self.task_id = task_id
        self.assigned_to = assigned_to


# # Define the Assignment model
# class Assignment(Document):
#     _id = ObjectIdField()  # Unique ID of the assignment
#     assignedBy = ObjectIdField()  # ID of the user who assigned the task
#     name = StringField()  # Name of the assignment
#     taskID = ObjectIdField()  # ID of the task
#     assignedTo = ListField(ObjectIdField())  # List of IDs of the users to whom the task is assigned

# # Define the Member model
# class Member(Document):
#     _id = ObjectIdField()  # Unique ID of the member
#     name = StringField()  # Name of the member
#     teamID = ObjectIdField()  # ID of the team to which the member belongs
#     role = StringField()  # Role of the member in the team

# # Define the Project model
# class Project(Document):
#     _id = ObjectIdField()  # Unique ID of the project
#     name = StringField()  # Name of the project
#     managerID = ObjectIdField()  # ID of the manager of the project
#     status = StringField()  # Status of the project

# # Define the Job model
# class Job(EmbeddedDocument):
#     job = StringField()  # Name of the job
#     deadline = DateTimeField()  # Deadline of the job
#     status = BooleanField()  # Status of the job

# # Define the Task model
# class Task(Document):
#     _id = ObjectIdField()  # Unique ID of the task
#     name = StringField()  # Name of the task
#     projectID = ObjectIdField()  # ID of the project to which the task belongs
#     billable = BooleanField()  # Whether the task is billable
#     deadline = DateTimeField()  # Deadline of the task
#     joblist = ListField(EmbeddedDocumentField(Job))  # List of jobs in the task
#     description = StringField()  # Description of the task
#     status = BooleanField()  # Status of the task

# # Define the Team model
# class Team(Document):
    _id = ObjectIdField()  # Unique ID of the team
    name = StringField()  # Name of the team
    projectID = ObjectIdField()  # ID of the project to which the team belongs
    leadID = ObjectIdField()  # ID of the team lead