from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
# from .models import EmployeeSheet
client = MongoClient('mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority&appName=EmployeePortal', server_api=ServerApi('1'), UuidRepresentation="standard")

class WorkDay:
    def __init__(self, work: bool):
        self.work = work
        self.hour = int(0)
        self.comment = str("")

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
class EmployeeSheet:
    def __init__(self, employeeID: ObjectId, managerID: ObjectId, startDate: datetime, endDate: datetime, employeeSheetObject: list[EmployeeSheetObject] = []):
        self.employeeID = employeeID
        self.managerID = managerID
        self.startDate = startDate
        self.endDate = endDate
        self.employeeSheetObject = employeeSheetObject
        self.status = "Testing"
    def to_dict(self):
        return {
            "employeeID": self.employeeID,
            "managerID": self.managerID,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "employeeSheetObject": [vars(employeeSheetInstance) for employeeSheetInstance in self.employeeSheetObject],
            "status": self.status
        } 

def get_next_week():
    # Get the current date and time
    current_date = datetime.now()
    # Calculate the number of days until the next Monday
    days_until_next_monday = 7 - current_date.weekday() if current_date.weekday() > 0 else 1
    # Add the number of days until the next Monday to the current date
    next_monday = current_date + timedelta(days=days_until_next_monday)
    # Get the date of the next Monday at midnight
    next_monday_midnight = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    # Get the date of the next to next Monday at midnight
    next_to_next_monday_midnight = next_monday_midnight.replace(hour=23, minute=59, second=59, microsecond=59) + timedelta(days=6)
    return next_monday_midnight, next_to_next_monday_midnight

employee_sheets_collection = client.TimesheetDB.EmployeeSheets
employee_collection = client.WorkBaseDB.Members
# Get next week
next_monday, next_to_next_monday = get_next_week()
currentDate = datetime.now()

# format dates
# endDate = datetime.strptime(data['endDate'], "%Y-%m-%d %H:%M:%S")
next_monday = next_monday.strftime("%Y-%m-%d %H:%M:%S")
next_to_next_monday = next_to_next_monday.strftime("%Y-%m-%d %H:%M:%S")

# find list of all employees in employee collection where isEmployee is true
employees = list(employee_collection.find({"isEmployee": True},{"employeeID": "$_id", "managerID": "$reportsTo"}))
for employee in employees:
    new_employeeSheet = EmployeeSheet(employeeID=employee["employeeID"], managerID=employee["managerID"], startDate=next_monday, endDate=next_to_next_monday)
    # check if employeeSheet exists for the same duration for same employee
    current_employeeSheet = employee_sheets_collection.find_one({"employeeID": employee["employeeID"], "startDate": next_monday, "endDate": next_to_next_monday})
    # create timesheet for all employees
    if not current_employeeSheet:
        result = employee_sheets_collection.insert_one(new_employeeSheet.to_dict())
        if (result):
            print("Employee Sheet Created"+": EmployeeSheetID :"+ str(result.inserted_id))
        else:
            print("Employee Sheet Creation Failed")
    else:
        print("Employee Sheet Already Exists")