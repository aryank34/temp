from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
employeeSheetID = ObjectId("65d64e0c8dd84d95f68a436b")
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

class ManagerSheetReview:
    def __init__(self, status: str, employeeSheetID: ObjectId):
        self.employeeSheetID = employeeSheetID
        self.status = status
    def to_dict(self):
        return {
            "employeeSheetID": self.employeeSheetID,
            "status": self.status
        }

timesheets = list(client.TimesheetDB.EmployeeSheets.find({"status": "Ongoing"}))

if len(timesheets) == 0:
    print("No timesheets found")
    exit()

for timesheet in timesheets:
    if timesheet["employeeSheetInstances"][len(timesheet["employeeSheetInstances"])-1]["employeeSheetObject"]["workDay"]["sun"]["work"] == False and timesheet["employeeSheetInstances"][len(timesheet["employeeSheetInstances"])-1]["employeeSheetObject"]["workDay"]["sun"]["work"] == False:
        # submit the timesheet for review
        client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet["_id"]}, {"$set": {"status": "Reviewing"}})
        # create new ManagerSheetReview document
        managerSheetReview = ManagerSheetReview(status="Review", employeeSheetID=timesheet["_id"])
        newManagerSheetReview = client.TimesheetDB.ManagerSheets.insert_one(managerSheetReview.to_dict())
        # update the TimesheetRecords for the new ManagerSheet, replacing the old ManagerSheet with the new one
        # create new managerSheetsInstance 
        document = client.TimesheetDB.TimesheetRecords.find_one({"managerID": timesheet['managerID'], "managerSheetsInstances.managerSheetsObjects": timesheet['managerSheetID']})
        if document:
            # If managerSheetObject exists, remove it
            client.TimesheetDB.TimesheetRecords.update_one(
                {"managerID": timesheet['managerID']},
                {"$pull": {"managerSheetsInstances": {"managerSheetsObjects": timesheet['managerSheetID']}}}
            )
        # Add the new managerSheetObject
        # client.TimesheetDB.TimesheetRecords.update_one({"managerID": timesheet['managerID']}, {"$push": {"managerSheetsInstances": {"managerSheetsObjects": newManagerSheetReview.inserted_id, "lastUpdateDate": datetime.now()}}})
        client.TimesheetDB.TimesheetRecords.update_one(
            {"managerID": timesheet['managerID'],},
            {"$push": {"managerSheetsInstances": {
                "managerSheetsObjects": newManagerSheetReview.inserted_id,
                "lastUpdateDate": datetime.now(),
                "version": timesheet["managerSheetsInstances"][len(timesheet["managerSheetsInstances"])-1]["version"]
            }}}
        )
print("Timesheets submitted for Review")