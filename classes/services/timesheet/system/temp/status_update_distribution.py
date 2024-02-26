from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
employeeSheetID = ObjectId("65d64e0c8dd84d95f68a436b")
client = MongoClient('mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority&appName=EmployeePortal', server_api=ServerApi('1'), UuidRepresentation="standard")

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
    next_to_next_monday_midnight = next_monday_midnight + timedelta(days=7)

    return next_monday_midnight, next_to_next_monday_midnight

manager_sheets_collection = client.TimesheetDB.ManagerSheets

# Get next week
next_monday, next_to_next_monday = get_next_week()

# Find all documents where the startDate is in the next week
documents_active = list(manager_sheets_collection.find({"startDate": {"$gte": next_monday, "$lt": next_to_next_monday},"status": "Upcoming"}, {"_id": 1}))

if len(documents_active) == 0:
    print("No documents found")
    exit()

# in ManagerSheets, update all these documents_active status to active
for document in documents_active:
    manager_sheets_collection.update_one({"_id": document["_id"]}, {"$set": {"status": "Active"}})

currentDate = datetime.now()
# Find all documents where the startDate is in the next week
documents_draft = list(manager_sheets_collection.find({"startDate": {"$lt": currentDate},"status": "Upcoming"}, {"_id": 1}))

# in ManagerSheets, update all these documents_draft status to active
for document in documents_draft:
    manager_sheets_collection.update_one({"_id": document["_id"]}, {"$set": {"status": "Draft"}})
print("Status Update Completed")