# Import necessary modules from flask_mongoengine and mongoengine
# from flask_mongoengine import MongoEngine
# from mongoengine import Document, EmbeddedDocument, StringField, BooleanField, IntField, DictField, EmbeddedDocumentField, DateTimeField, ObjectIdField, ListField

# Create an instance of MongoEngine
# db = MongoEngine()

from datetime import datetime
from bson.objectid import ObjectId

class ManagerSheetsInstance:
    def __init__(self, created_date: datetime, manager_sheets_objectID: ObjectId):
        self.created_date = created_date
        self.manager_sheets_objects = manager_sheets_objectID
    def to_dict(self):
        return {
            "created_date": self.created_date.isoformat(),
            "manager_sheets_objects": str(self.manager_sheets_objects)
        }

class TimesheetRecord:
    def __init__(self, manager_id: ObjectId, manager_sheets_instances: list[ManagerSheetsInstance]):
        # self._id = _id
        self.manager_id = manager_id
        self.manager_sheets_instances = manager_sheets_instances
    def to_dict(self):
        return {
            "manager_id": self.manager_id,
            "manager_sheets_instances": [vars(manager_sheets_instance) for manager_sheets_instance in self.manager_sheets_instances]
        }
class WorkDay:
    def __init__(self, work: bool, hour: int, comment: str):
        self.work = work
        self.hour = hour
        self.comment = comment

class ManagerSheetsAssign:
    def __init__(self, project_id: ObjectId, start_date: datetime, end_date: datetime, work_day: dict[str, WorkDay], description: str, status: str, assign_group_id: ObjectId, sheet_update: bool):
        # self._id = _id
        self.project_id = project_id
        self.start_date = start_date
        self.end_date = end_date
        self.work_day = work_day
        self.description = description
        self.status = status
        self.assign_group_id = assign_group_id
        self.sheet_update = sheet_update
    
    def to_dict(self):
        return {
            "project_id": self.project_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "work_day": {day: vars(work_day) for day, work_day in self.work_day.items()},
            "description": self.description,
            "status": self.status,
            "assign_group_id": self.assign_group_id,
            "sheet_update": self.sheet_update
        }

class EmployeeSheetObject:
    def __init__(self, project_id: ObjectId, task_id: ObjectId, work_day: dict[str, WorkDay], description: str):
        self.project_id = project_id
        self.task_id = task_id
        self.work_day = work_day
        self.description = description

class EmployeeSheetInstance:
    def __init__(self, version: int, employee_sheet_object: EmployeeSheetObject):
        self.version = version
        self.employee_sheet_object = employee_sheet_object

class ManagerSheetReview:
    def __init__(self, status: str, employee_sheet_id: ObjectId, employee_id: ObjectId, start_date: datetime, end_date: datetime, employee_sheet_instances: list[EmployeeSheetInstance]):
        # self._id = _id
        self.status = status
        self.employee_sheet_id = employee_sheet_id
        self.employee_id = employee_id
        self.start_date = start_date
        self.end_date = end_date
        self.employee_sheet_instances = employee_sheet_instances

class EmployeeSheet:
    def __init__(self, manager_sheet_id: ObjectId, employee_id: ObjectId, manager_id: ObjectId, start_date: datetime, end_date: datetime, employee_sheet_instances: list[EmployeeSheetInstance], status: str):
        # self._id = _id
        self.manager_sheet_id = manager_sheet_id
        self.employee_id = employee_id
        self.manager_id = manager_id
        self.start_date = start_date
        self.end_date = end_date
        self.employee_sheet_instances = employee_sheet_instances
        self.status = status

class AssignmentInstance:
    def __init__(self, assign_date: datetime, assignment_id: ObjectId):
        self.assign_date = assign_date
        self.assignment_id = assignment_id

class AssignmentGroup:
    def __init__(self, name: str, assignment_instances: list[AssignmentInstance]):
        # self._id = _id
        self.name = name
        self.assignment_instances = assignment_instances







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