# Import ThreadPoolExecutor from concurrent.futures for creating a pool of worker threads
from concurrent.futures import ThreadPoolExecutor
# Import datetime and timedelta from datetime for working with dates and times
from datetime import datetime, timedelta
# Import time for working with time
import time
# Import logging for logging messages to a file
import logging
# Import ObjectId from bson for creating unique identifiers in MongoDB
from bson import ObjectId
# Import pandas for data manipulation and analysis
import pandas as pd
# Import MongoClient from pymongo for connecting to a MongoDB server
from pymongo import MongoClient
# Import BackgroundScheduler from apscheduler.schedulers.background for scheduling jobs to run in the background
from apscheduler.schedulers.background import BackgroundScheduler
# Import jsonify and make_response from flask for creating JSON responses
from flask import jsonify, make_response
# Import os for interacting with the operating system
import os# Import MongoClient from pymongo for connecting to a MongoDB server (duplicate import, can be removed)
from pymongo import MongoClient
# Import ServerApi from pymongo.server_api for specifying the MongoDB server API version
from pymongo.server_api import ServerApi
# Import find_dotenv and load_dotenv from dotenv for loading environment variables from a .env file
from dotenv import find_dotenv, load_dotenv
# Load environment variables from a .env file
load_dotenv(find_dotenv())# Get the MongoDB host URI from environment variables
mongo_host = os.environ.get("MONGO_HOST_prim")

# Get the directory that contains the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)
# Join the parent directory with the file name
kill_file_path = os.path.join(parent_dir, 'kill_timesheet_sync.txt')
log_file_path = os.path.join(parent_dir, 'logfile.log')
logging.basicConfig(filename=log_file_path, filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  # Set the logging configuration    

# -------------------------------------------------------------------------------------
# Define a class for managing sheet instances
class ManagerSheetsInstance:
    def __init__(self, lastUpdateDate: datetime, managerSheetsObjectID: ObjectId, version: int = 0):  # Initialize the class with last update date, sheet object ID and version
        self.managerSheetsObjects = managerSheetsObjectID  # Assign the sheet object ID
        self.lastUpdateDate = lastUpdateDate  # Assign the last update date
        self.version = version  # Assign the version
    def to_dict(self):  # Convert the instance to a dictionary
        return {
            "managerSheetsObjects": self.managerSheetsObjects,
            "lastUpdateDate": self.lastUpdateDate,
            "version": self.version
        }
# Define a class for timesheet records
class TimesheetRecord:
    def __init__(self, managerID: ObjectId, managerSheetsInstances: list[ManagerSheetsInstance]):  # Initialize the class with manager ID and sheet instances
        self.managerID = managerID  # Assign the manager ID
        self.managerSheetsInstances = managerSheetsInstances  # Assign the sheet instances
    def to_dict(self):  # Convert the record to a dictionary
        return {
            "managerID": self.managerID,
            "managerSheetsInstances": [vars(managerSheetsInstance) for managerSheetsInstance in self.managerSheetsInstances]
        }
# Define a class for work days
class WorkDay:
    def __init__(self, work: bool):  # Initialize the class with a boolean indicating whether it's a work day
        self.work = work  # Assign the work day status
        self.hour = int(0)  # Initialize the hour as 0
        self.comment = str("")  # Initialize the comment as an empty string
# Define a class for managing sheet assignments
class ManagerSheetsAssign:
    def __init__(self, projectID: ObjectId, startDate: datetime, endDate: datetime, workDay: dict[str, WorkDay], description: str, status: str, assignGroupID: ObjectId):  # Initialize the class with project ID, start date, end date, work day, description, status, and assignment group ID
        self.projectID = projectID  # Assign the project ID
        self.startDate = startDate  # Assign the start date
        self.endDate = endDate  # Assign the end date
        self.workDay = workDay  # Assign the work day
        self.description = description  # Assign the description
        self.status = status  # Assign the status
        self.assignGroupID = assignGroupID  # Assign the assignment group ID
    def to_dict(self):  # Convert the assignment to a dictionary
        return {
            "projectID": self.projectID,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "workDay": {day: vars(workDay) for day, workDay in self.workDay.items()},
            "description": self.description,
            "status": self.status,
            "assignGroupID": self.assignGroupID,
        }
# Define a class for managing sheet reviews
class ManagerSheetReview:
    def __init__(self, status: str, employeeSheetID: ObjectId):  # Initialize the class with status and employee sheet ID
        self.employeeSheetID = employeeSheetID  # Assign the employee sheet ID
        self.status = status  # Assign the status
    def to_dict(self):  # Convert the review to a dictionary
        return {
            "employeeSheetID": self.employeeSheetID,
            "status": self.status
        }
# Define a class for assignment instances
class AssignmentInstance:
    def __init__(self, assignDate: datetime, assignmentID: ObjectId):  # Initialize the class with assignment date and assignment ID
        self.assignDate = assignDate  # Assign the assignment date
        self.assignmentID = assignmentID  # Assign the assignment ID
# Define a class for assignment groups
class AssignmentGroup:
    def __init__(self, name: str, assignmentInstances: list[AssignmentInstance]):  # Initialize the class with name and assignment instances
        self.name = name  # Assign the name
        self.assignmentInstances = assignmentInstances  # Assign the assignment instances
# Define a class for employee sheet objects
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
# Define a class for employee sheets
class EmployeeSheet:
    def __init__(self, employeeID: ObjectId, managerID: ObjectId, startDate: datetime, endDate: datetime, employeeSheetObject: list[EmployeeSheetObject] = []):
        self.employeeID = employeeID
        self.managerID = managerID
        self.startDate = startDate
        self.endDate = endDate
        self.employeeSheetObject = employeeSheetObject
        self.status = "Submission_Check"
    def to_dict(self):
        return {
            "employeeID": self.employeeID,
            "managerID": self.managerID,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "employeeSheetObject": [vars(employeeSheetInstance) for employeeSheetInstance in self.employeeSheetObject],
            "status": self.status
        } 
# --------------------------------------------------------------------------------------

# Function to check the connection to the MongoDB server
def dbConnectCheck():
    """
    This function creates a new MongoDB client and checks the connection to the MongoDB server.
    It returns the MongoClient instance if the connection is successful, or an error response if the connection fails.
    """
    try:
        logging.info("[INIT] --- Connecting to MongoDB")
        uri = mongo_host  # Get the MongoDB host URI
        client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")  # Create a new MongoDB client using the host URI, server API version, and UUID representation
        logging.info('[OK] --- Connection to MongoDB server successful.')
        return client  # Return the client if the connection is successful

    except Exception as e:
        logging.error("[ERROR] --- Failed to connect to MongoDB server: ",type(e).__name__, ":", str(e))
        return make_response(jsonify({"error": str(e)}), 500)  # Return an error response if the connection fails

# Function to get the date of the next Monday at midnight    
def get_next_week():
    '''
    This function calculates the date of the next Monday at midnight and the date of the next to next Monday at midnight.
    It returns the dates of the next Monday and the next to next Monday at midnight.
    '''
    current_date = datetime.now()  # Get the current date and time

    # Calculate the number of days until the next Monday
    # If today is Monday, set it to 1, else calculate the remaining days of the week
    days_until_next_monday = 7 - current_date.weekday() if current_date.weekday() > 0 else 1

    next_monday = current_date + timedelta(days=days_until_next_monday)  # Add the number of days until the next Monday to the current date

    # Get the date of the next Monday at midnight by replacing the hour, minute, second, and microsecond of next_monday with 0
    next_monday_midnight = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get the date of the next to next Monday at midnight by adding 7 days to next_monday_midnight
    next_to_next_monday_midnight = next_monday_midnight + timedelta(days=7)

    return next_monday_midnight, next_to_next_monday_midnight  # Return the dates of the next Monday and the next to next Monday at midnight

# Function to update the status of upcoming timesheets to active
def update_status_timesheets():
    try:
        logging.info("[INIT] --- Updating Status of Upcoming Timesheets...")  # Log the start of the status update process
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            manager_sheets_collection = client.TimesheetDB.ManagerSheets  # Get the ManagerSheets collection

            next_monday, next_to_next_monday = get_next_week()  # Get the dates of the next Monday and the next to next Monday

            # Find all documents where the startDate is in the next week and the status is "Upcoming"
            documents_active = list(manager_sheets_collection.find({"startDate": {"$gte": next_monday, "$lt": next_to_next_monday},"status": "Upcoming"}, {"_id": 1}))

            # Update the status of all these documents to "Active"
            for document in documents_active:
                manager_sheets_collection.update_one({"_id": document["_id"]}, {"$set": {"status": "Active"}})

            currentDate = datetime.now()  # Get the current date and time

            # Find all documents where the startDate is before the current date and the status is "Upcoming"
            documents_draft = list(manager_sheets_collection.find({"startDate": {"$lt": currentDate},"status": "Upcoming"}, {"_id": 1}))

            # Update the status of all these documents to "Draft"
            for document in documents_draft:
                manager_sheets_collection.update_one({"_id": document["_id"]}, {"$set": {"status": "Draft"}})
            
            logging.info("[OK] --- Status Update Completed.")  # Log a success message
        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while updating status of timesheets.")
    except Exception as e:
        # If an error occurs, log the error message
        logging.error("Error updating status of timesheets: ",type(e).__name__, ":", str(e))

# # Function to store employee sheets in the database
# def store_employee_sheets(data, client):
#     try:
#         logging.info("Storing employee sheets in the database...")
        
#         # Create WorkDay object for each day of the week
#         workDay = {
#             "mon": WorkDay(data["workDay"]["mon"]["work"]),
#             "tue": WorkDay(data["workDay"]["tue"]["work"]),
#             "wed": WorkDay(data["workDay"]["wed"]["work"]),
#             "thu": WorkDay(data["workDay"]["thu"]["work"]),
#             "fri": WorkDay(data["workDay"]["fri"]["work"]),
#             "sat": WorkDay(data["workDay"]["sat"]["work"]),
#             "sun": WorkDay(data["workDay"]["sun"]["work"]),
#         }
        
#         # Extract projectID, taskID, and description from the data
#         projectID = ObjectId(data["Project"]["projectID"])
#         taskID = ObjectId(data["Task"]["taskID"])
#         description = data["description"]

#         # Create an EmployeeSheetObject with the extracted data and the created WorkDay object
#         employeeSheetObject = EmployeeSheetObject(projectID=projectID, taskID=taskID, workDay=workDay, description=description)
        
#         # Extract version from the data
#         version = data["version"]
        
#         # Create an EmployeeSheetInstance with the extracted version and the created EmployeeSheetObject
#         employeeSheetInstance = EmployeeSheetInstance(version=version, employeeSheetObject=employeeSheetObject)

#         # Extract managerSheetID, employeeID, managerID, startDate, and endDate from the data
#         managerSheetID = ObjectId(data["managerSheetID"])
#         employeeID = ObjectId(data["Employee"]["employeeID"])
#         managerID = ObjectId(data["Manager"]["managerID"])
#         startDate = data["startDate"]
#         endDate = data["endDate"]
        
#         # Create an EmployeeSheet with the extracted data and the created EmployeeSheetInstance
#         employeeSheet = EmployeeSheet(managerSheetID=managerSheetID, employeeID=employeeID, managerID=managerID, startDate=startDate, endDate=endDate, employeeSheetInstances=[employeeSheetInstance])
#         logging.info("EmployeeSheet Instance Generated")
        
#         msg_str = ""

#         # Check if an EmployeeSheet with the same managerSheetID and employeeID already exists in the database
#         if (client.TimesheetDB.EmployeeSheets.find_one({"managerSheetID": employeeSheet.managerSheetID, "employeeID": employeeSheet.employeeID}) is None):
#             # If not, insert the created EmployeeSheet into the database and log a success message
#             result = client.TimesheetDB.EmployeeSheets.insert_one(employeeSheet.to_dict())
#             msg_str = "Employee Sheet Created" + ": EmployeeSheetID :" + str(result.inserted_id)
#             # logging.info("Inserted the created EmployeeSheet into the database with the created EmployeeSheet Instance")
#         else:
#             # If an EmployeeSheet with the same managerSheetID and employeeID already exists, check if an EmployeeSheetInstance with the same version already exists
#             if (client.TimesheetDB.EmployeeSheets.find_one({"employeeSheetInstances.version": version}) is None):
#                 # If not, update the existing EmployeeSheet with the created EmployeeSheetInstance and log a success message
#                 result = client.TimesheetDB.EmployeeSheets.update_one({"employeeID": employeeSheet.employeeID, "managerSheetID": employeeSheet.managerSheetID},
#                                                             {"$push": {"employeeSheetInstances": employeeSheetInstance.to_dict()}})
#                 msg_str = "Employee Sheet updated" + ": EmployeeSheetID :" + str(result.inserted_id)
#                 # logging.info("Updated the existing EmployeeSheet with the created EmployeeSheet Instance")
#             else:
#                 # If an EmployeeSheetInstance with the same version already exists, log a message indicating that the EmployeeSheet already exists
#                 msg_str = "Employee Sheet already exists"
#                 # logging.info("EmployeeSheet Instance already exists")
        
#         logging.info(msg_str)  # Log the message
#     except Exception as e:
#         # If an error occurs, log an error message
#         logging.error("[ERROR] --- Error creating Timesheet Records: ",type(e).__name__, ":", str(e))
        
# # Function to distribute active timesheets
# def distribute_active_timesheets():
#     try:
#         logging.info("[INIT] --- Timesheets Distribution Initiated...")
#         client = dbConnectCheck()  # Check the database connection
#         if isinstance(client, MongoClient):  # If the connection is successful
#             # Define the pipeline for the aggregation operation on the TimesheetRecords collection
#             managerSheet_pipeline = [
#                 {"$unwind": "$managerSheetsInstances"},
#                 {"$lookup":{"from": "ManagerSheets",
#                             "localField": "managerSheetsInstances.managerSheetsObjects",
#                             "foreignField": "_id",
#                             "as": "manager"}},
#                 {"$unwind": "$manager"},
#                 {"$match":{ "manager.status": "Active"}},
#                 {"$lookup":{"from": "AssignmentGroup",
#                             "localField": "manager.assignGroupID",
#                             "foreignField": "_id",
#                             "as": "assign"}},
#                 {"$unwind": "$assign"},
#                 {"$project":{"managerID": 1,
#                             "version": "$managerSheetsInstances.version",
#                             "managerSheetID": "$managerSheetsInstances.managerSheetsObjects",
#                             "startDate": "$manager.startDate",
#                             "endDate": "$manager.endDate",
#                             "status": "$manager.status",
#                             "projectID": "$assign.projectID",
#                             "workDay": "$manager.workDay",
#                             "description": "$manager.description",
#                             "assignmentID": "$assign.assignmentInstances.assignmentID"}},
#                 {"$unwind": "$assignmentID"}
#             ]

#             # Define the pipeline for the aggregation operation on the Assignments collection
#             assignment_pipeline = [
#                 {"$unwind": "$assignedTo"},
#                 {"$lookup":{"from": "Members",
#                             "localField": "assignedTo",
#                             "foreignField": "_id",
#                             "as": "member"}},
#                 {"$unwind": "$member"},
#                 {"$lookup":{"from": "Members",
#                             "localField": "assignedBy",
#                             "foreignField": "_id",
#                             "as": "manager"}},
#                 {"$unwind": "$manager"},
#                 {"$lookup":{"from": "Tasks",
#                             "localField": "taskID",
#                             "foreignField": "_id",
#                             "as": "task"}},
#                 {"$unwind": "$task"},
#                 {"$lookup":{"from": "Projects",
#                             "localField": "projectID",
#                             "foreignField": "_id",
#                             "as": "project"}},
#                 {"$unwind": "$project"},
#                 {"$project":{"_id":0,
#                             "assignmentID": "$_id",
#                             "Assignment Name": "$name",
#                             "Project":{"projectID": "$project._id",
#                                         "Project Name": "$project.name"},
#                             "Task":{   "taskID": "$task._id",
#                                         "Task Name": "$task.name",
#                                         "Billable": "$task.billable",
#                                         "Task Description": "$task.description",},
#                             "Employee":{"employeeID": "$member._id",
#                                         "Employee Name": "$member.name"},
#                             "Manager":{"managerID": "$manager._id",
#                                         "Manager Name": "$manager.name"}}}
#             ]

#             # Perform the aggregation operations and convert the results to lists
#             timesheet_documents = list(client.TimesheetDB.TimesheetRecords.aggregate(managerSheet_pipeline))
#             assignment_documents = list(client.WorkBaseDB.Assignments.aggregate(assignment_pipeline))

#             # Convert the lists to DataFrames
#             timesheet_df = pd.DataFrame(timesheet_documents)
#             assignment_df = pd.DataFrame(assignment_documents)

#             # Merge the DataFrames on the 'assignmentID' column
#             result_df = pd.merge(timesheet_df, assignment_df, on='assignmentID', how='inner')

#             # Convert the merged DataFrame to a list of dictionaries
#             result_documents = result_df.to_dict(orient='records')

#             # For each dictionary in the list, extract a subset of the key-value pairs and store the resulting dictionary in the database
#             for i in range(len(result_documents)):
#                 subset_dict = {key: result_documents[i][key] for key in ['managerSheetID', 'startDate', 'endDate', 'status', 'version', 'workDay', 'description', 'Project', 'Task', 'Employee', 'Manager'] if key in result_documents[i]}
#                 store_employee_sheets(subset_dict, client)
#             logging.info("[OK] --- Completed updating employee sheets in the database")
#             logging.info("[OK] --- Timesheets Distribution Successful")  # Log a success message
#         else:
#             # If the connection fails, log an error message
#             logging.error("[ERROR] --- Failed to connect to the MongoDB server while distributing timesheets")
#     except Exception as e:
#         # If an error occurs, log an error message
#         logging.error("[ERROR] --- Error distributing timesheets: ",type(e).__name__, ":", str(e))

def create_employee_sheets():
    try:
        logging.info("[INIT] --- Creating Employee Sheets...")  # Log the start of the process
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Get next week
            next_monday, next_to_next_monday = get_next_week()

            # format dates
            next_monday = next_monday.strftime("%Y-%m-%d %H:%M:%S")
            next_to_next_monday = next_to_next_monday.strftime("%Y-%m-%d %H:%M:%S")

            # find list of all employees in employee collection where isEmployee is true
            employees = list(client.WorkBaseDB.Members.find({"isEmployee": True},{"employeeID": "$_id", "managerID": "$reportsTo"}))
            for employee in employees:
                new_employeeSheet = EmployeeSheet(employeeID=employee["employeeID"], managerID=employee["managerID"], startDate=next_monday, endDate=next_to_next_monday)
                # check if employeeSheet exists for the same duration for same employee
                current_employeeSheet = client.TimesheetDB.EmployeeSheets.find_one({"employeeID": employee["employeeID"], "startDate": next_monday, "endDate": next_to_next_monday})
                # create timesheet for all employees
                if not current_employeeSheet:
                    result = client.TimesheetDB.EmployeeSheets.insert_one(new_employeeSheet.to_dict())
                    if (result):
                        logging.info("[OK] --- Employee Sheet Created"+" : EmployeeSheetID : "+ str(result.inserted_id), " : EmployeeID : "+ str(employee["employeeID"]))
                    else:
                        logging.error("[ERROR] --- Employee Sheet Creation Failed"+" : EmployeeID : "+ str(employee["employeeID"]))
                else:
                    logging.info("[INFO] --- Employee Sheet Already Exists"+" : EmployeeID : "+ str(employee["employeeID"]))

        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while creating employee sheets")
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error creating employee sheets: ",type(e).__name__, ":", str(e))

def auto_submit_timesheet():
    try:        
        # create EmployeeSheets for everyone
        create_employee_sheets()
        # attempt to submit and obtain list of employeeIDs who have not submitted timesheets yet
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Get the current date and time
            currentDate = datetime.now()
        else: # Otherwise
            # Log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while auto-submitting timesheets")
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error auto-submitting timesheets: ",type(e).__name__, ":", str(e))
# Function to submit timesheets for review
def submit_timesheet_for_review(week_check):
    try:
        logging.info("[INIT] --- Timesheets Submission Process Initialed...")  # Log a success message

        client = dbConnectCheck()  # Check the database connection
        logging.info("Collecting timesheets for submission...")  # Log the start of the process
        if isinstance(client, MongoClient):  # If the connection is successful
            if week_check:  # If week_check is True
                timesheets = get_weekend_timesheets()  # Get the timesheets for the weekend
            else:  # If week_check is False
                timesheets = get_default_timesheets()  # Get the default timesheets
            logging.info("[OK] --- Timesheets collected for submission")  # Log a success message
            # Get the number of timesheets collected for submission
            sheets_count = len(timesheets) # Get the number of timesheets collected
            logging.info(f"Number of timesheets collected for submission: {sheets_count}")  # Log the number of timesheets collected for submission
            logging.info("Attempting submission...")  # Log the start of the process
            success_count = 0  # Variable to keep track of successful thread executions
            with ThreadPoolExecutor() as executor:  # Create a ThreadPoolExecutor
                # Use the executor to submit the timesheets for review in parallel
                results = executor.map(submit_timesheet_for_review_thread, [(timesheet) for timesheet in timesheets])
            for result in results:
                if result is not None:
                    success_count += 1
            if success_count == sheets_count:
                logging.info("[OK] --- All timesheets submitted for Review")  # Log a success message
            else:
                # print the number of successfuly submitted sheets out of total sheets
                logging.info(f"[INFO] Number of timesheets submitted for review: {success_count} out of {sheets_count}")
        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while timesheet submission")
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error submitting timesheets for review: ",type(e).__name__, ":", str(e))

# Function to submit timesheets for review at a thread
def submit_timesheet_for_review_thread(timesheet):
    try:
        logging.info("Running SubmitTimesheetForReviewThread...")  # Log the start of the thread
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # last_instance = timesheet["employeeSheetInstances"][-1]  # Get the last instance of the timesheet

            # Create a new ManagerSheetReview document with the status set to "Review" and the employeeSheetID set to the ID of the timesheet
            managerSheetReview = ManagerSheetReview(status="Review", employeeSheetID=timesheet["_id"])
            newManagerSheetReview = client.TimesheetDB.ManagerSheets.insert_one(managerSheetReview.to_dict())  # Insert the new ManagerSheetReview document into the database
            
            # Add the new ManagerSheetReview document to the TimesheetRecords collection
            client.TimesheetDB.TimesheetRecords.update_one(
                {"managerID": timesheet['managerID']},
                {"$push": {"managerSheetsInstances": {
                    "managerSheetsObjects": newManagerSheetReview.inserted_id,
                    "lastUpdateDate": datetime.now(),
                    "version": 0
                }}}
            )

            # Update the status of the ManagerSheet document to "Draft"
            client.TimesheetDB.ManagerSheets.update_one({"_id": timesheet["managerSheetID"]}, {"$set": {"status": "Draft"}})

            # Update the status of the EmployeeSheet document to "Reviewing" and set the managerSheetID to the ID of the new ManagerSheetReview document
            client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet["_id"]}, {"$set": {"status": "Reviewing", "managerSheetID": newManagerSheetReview.inserted_id}})

            logging.info("[OK] --- Submission Successful")  # Log a success message
            return True
        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while timesheet submission at a thread")
            return None
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error submitting timesheets for review at a thread: ",type(e).__name__, ":", str(e))
        return None

# Function to get default timesheets
def get_default_timesheets():
    try:
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Find all EmployeeSheets documents where the status is "Submitted" and both Saturday and Sunday are not work days
            default_timesheets = list(client.TimesheetDB.EmployeeSheets.find({"status": "Ongoing", 
                                                                            "$and": [{"employeeSheetObject": {"$elemMatch": {"workDay.sat.work": False}}},
                                                                                    {"employeeSheetObject": {"$elemMatch": {"workDay.sun.work": False}}}]})
            )
            return default_timesheets  # Return the found documents
        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while getting default timesheets")
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error getting default timesheets: ",type(e).__name__, ":", str(e))

# Function to get weekend timesheets
def get_weekend_timesheets():
    try:        
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Find all EmployeeSheets documents where the status is "Submitted" and either Saturday or Sunday is a work day
            weekend_timesheets = list(client.TimesheetDB.EmployeeSheets.find({"status": "Ongoing", 
                                                                            "$or": [{"employeeSheetObject": {"$elemMatch": {"workDay.sat.work": True}}},
                                                                                    {"employeeSheetObject": {"$elemMatch": {"workDay.sun.work": True}}}]})
            )
            return weekend_timesheets  # Return the found documents
        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while getting weekend timesheets")
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error getting weekend timesheets: ",type(e).__name__, ":", str(e))

# def friday_submitted_timesheets_check():
#     try:
#         logging.info("[INIT] --- Timesheets Submission Checking Protocol Initiated...")
#         client = dbConnectCheck()  # Check the database connection
#         if isinstance(client, MongoClient):  # If the connection is successful
#             # Get the current date
#             now = datetime.now()
#             # Find the start and end of the current week
#             start_of_week = now - timedelta(days=now.weekday())
#             start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)  # Set time to 12AM
#             end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)  # Set time to 11:59PM
#             # Query the EmployeeSheets collection for all sheets with a startDate or endDate within the current week and a status of submitted or reviewing
#             employee_sheets_cursor = client.TimesheetDB.EmployeeSheets.find({
#                 '$and': [
#                     {'startDate': {'$gte': start_of_week, '$lte': end_of_week}},  # startDate is within the current week
#                     {'endDate': {'$gte': start_of_week, '$lte': end_of_week}},  # endDate is within the current week
#                     {'status': {'$in': ['Submitted', 'Reviewing']}}  # status is submitted or reviewing
#                 ]
#             })
#             # Convert the results to a list
#             employee_sheets = list(employee_sheets_cursor)
#             # Get the list of employees with a submitted or reviewing sheet status
#             employees_with_sheets = [sheet['employeeID'] for sheet in employee_sheets]

#             # Get the list of employees from the Members collection who are not included in the list of the reviewing and submitted timesheet status
#             members_cursor = client.WorkBaseDB.Members.find({
#                 '_id': {'$nin': employees_with_sheets},
#                 'name': {'$ne': 'ALL EMPLOYEES'}
#             })
#             # Convert the results to a list
#             members = list(members_cursor)
#             # Iterate over the employees who are not included in the list of the reviewing and submitted timesheet status
#             for member in members:
#                 # Get the employee's ID and manager's ID
#                 employee_id = member['_id']
#                 if 'reportsTo' in member:
#                     manager_id = member['reportsTo']
#                 else:
#                     manager_id = None

#                 # Create a new document with the employee's ID and the initial manager's ID
#                 document = {
#                     'employeeID': employee_id,
#                     'managerID': [manager_id]
#                 }

#                 # Insert the new document into the EscalationState collection
#                 document = client.TimesheetDB.EscalationState.insert_one(document)
#                 if (document):
#                     logging.info("[OK] --- Escalation State Created"+" : EscalationStateID : "+ str(document.inserted_id), " : EmployeeID : "+ str(employee_id))
                
#             logging.info("[OK] --- Timesheets Submission Checking Protocol Completed")  # Log a success message
        
#         else:
#             # If the connection fails, log an error message
#             logging.error("[ERROR] --- Failed to connect to the MongoDB server while checking submitted timesheets")
    
#     except Exception as e:
#         # If an error occurs, log an error message
#         logging.error("[ERROR] --- Error checking submitted timesheets: ",type(e).__name__, ":", str(e))

# Import ThreadPoolExecutor from concurrent.futures for creating a pool of worker threads
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId

from concurrent.futures import ThreadPoolExecutor

def publish_timesheet_escalation_notification_for_employee(managerID, employeeID, template, week_start_str, week_end_str):
    try:
        logging.info("[INIT] --- Performing Notification Publication for Employee: %s and Manager: %s" % (employeeID, managerID))
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Replace the placeholders in the template with the actual values
            manager_name = client.WorkBaseDB.Members.find_one({'_id': managerID})['name']
            employee_name = client.WorkBaseDB.Members.find_one({'_id': employeeID})['name']
            content = template['Contents']['message'].format(
                recipient_name=manager_name,  # Replace this with the actual manager name
                subject_name=employee_name,
                week_start=week_start_str,
                week_end=week_end_str
            )
            # Create the notification document
            notification = {
                'employeeID': employeeID,
                'title': template['template_name'],
                'date': datetime.now(),
                'content': content,
                'level': template['Level']
            }
            # Insert the notification document into the Notifications collection
            updated = client.NotificationDB.NotificationEvents.insert_one(notification)
            if updated:
                logging.info("[OK] - Notification created for employee ID: %s and manager ID: %s" % (employeeID, managerID))
                return True
            else:
                logging.error("[ERROR] - Failed to create notification for employee ID: %s and manager ID: %s" % (employeeID, managerID))
                return None
        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while creating notifications")
            return None
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error creating notifications: ",type(e).__name__, ":", str(e), " : EmployeeID : "+ str(employeeID), " : ManagerID : "+ str(managerID))
        return None

def create_timesheet_escalation_notification_for_member_thread(member, template, week_start_str, week_end_str):
    try:
        logging.info("[INIT] --- Timesheet Escalation Notification Publication Process Initiated...")
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            employeeID = member['employeeID']
            logging.info("[INFO] - Creating notifications for employee ID: %s" %(employeeID))
            # Get the employee's name and managers
            managers = member['managerID']
            if len(managers) == 0:
                logging.info("[INFO] - No managers found for employee ID: %s" %(employeeID))
                managers = []
            manager_count = len(managers)
            logging.info(f"[INFO] - Number of managers: {manager_count}")
            logging.info("Initiating Timesheet Escalation Notification Publishing Process for Employee: %s" %(member['employeeID']))  # Log the start of the process
            success_count = 0  # Variable to keep track of successful thread executions
            # create notification for the managers
            with ThreadPoolExecutor() as executor:
                results = executor.map(publish_timesheet_escalation_notification_for_employee,
                            [(managerID) for managerID in managers], 
                            [employeeID]*len(managers), 
                            [template]*len(managers), 
                            [week_start_str]*len(managers), 
                            [week_end_str]*len(managers))
            # Return the number of successful thread executions
            for result in results:
                if result is not None:
                    success_count += 1
            if success_count == manager_count:
                logging.info(f"[OK] --- All jobs succeeded ({success_count} out of {manager_count})")  # Log a success message
            else:
                logging.info(f"[INFO] --- {success_count} out of {manager_count} jobs succeeded")  # Log the number of successful jobs
            # create notification for the employee
            publish_timesheet_escalation_notification_for_employee(employeeID, employeeID, template, week_start_str, week_end_str)
            logging.info("[END] - Finished creating notifications for employee ID: %s" %(employeeID))
            return True

        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while creating notifications")
            return None
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error creating notifications: ",type(e).__name__, ":", str(e), " : EmployeeID : "+ str(member['employeeID']))
        return None

def create_timesheet_escalation_notifications():
    try:
        logging.info("[INIT] --- Timesheets Submission Checking Protocol Initiated...")
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            logging.info("[INFO] - Starting to create notifications")

            # Get the current week's start and end dates
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            week_end = week_start + timedelta(days=6)

            # Format the dates as strings
            week_start_str = week_start.strftime('%d %B, %Y')
            week_end_str = week_end.strftime('%d %B, %Y')

            # Get the template from the NotificationTemplates collection
            template = client.NotificationDB.NotificationTemplates.find_one({'template_code': '505'})
            if template is None:
                logging.error("[ERROR] - Template not found")
                return
            # Get all the members from the EscalationState collection
            members = list(client.TimesheetDB.EscalationState.find())
            if len(members) == 0:
                logging.error("[ERROR] - Members not found")
                return
            # number of members
            members_count = len(members)
            logging.info(f"[INFO] - Number of members: {members_count}")
            logging.info("Initiating Notification Publishing Process...")  # Log the start of the process
            success_count = 0  # Variable to keep track of successful thread executions
            # Use a ThreadPoolExecutor to insert documents concurrently
            # Use a ThreadPoolExecutor to create notifications concurrently
            with ThreadPoolExecutor() as executor:
                results = executor.map(create_timesheet_escalation_notification_for_member_thread, 
                                    [member for member in members],
                                    [template]*len(members), 
                                    [week_start_str]*len(members), 
                                    [week_end_str]*len(members))
            
            # Return the number of successful thread executions
            for result in results:
                if result is not None:
                    success_count += 1
            if success_count == members_count:
                logging.info(f"[OK] --- All jobs succeeded ({success_count} out of {members_count})")  # Log a success message
            else:
                logging.info(f"[INFO] --- {success_count} out of {members_count} jobs succeeded")  # Log the number of successful jobs

            logging.info("[END] - Finished creating notifications")

        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while creating notifications")
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error creating notifications: ",type(e).__name__, ":", str(e))

def escalation_updation_thread(member):
    try:
        logging.info("[INIT] --- Performing Escalation Protocol upon Employee: " + str(member['_id']))
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Get the employee's ID and manager's ID
            employee_id = member['_id']
            # Check if the member already exists in the EscalationState collection
            existing_document = client.TimesheetDB.EscalationState.find_one({'employeeID': employee_id})

            if existing_document is None:
                # If the member does not exist, insert a new document
                # If the member does not exist, insert a new document
                manager_id = member.get('reportsTo', None)
                document = {
                    'employeeID': employee_id,
                    'managerID': [manager_id] if ((manager_id is not None) and manager_id != employee_id) else []
                }
                document = client.TimesheetDB.EscalationState.insert_one(document)
                logging.info("[OK] --- Escalation State Created" + " : EscalationStateID : " + str(document.inserted_id), " : EmployeeID : " + str(employee_id))
            else:
                # If the member does exist, find the reportsTo of the topmost manager and add it to the managerID list
                if existing_document['managerID']:
                    topmost_manager = existing_document['managerID'][-1]
                else:
                    topmost_manager = None
                if topmost_manager is None:
                    topmost_manager_reports_to = None
                else:
                    topmost_manager_document = client.WorkBaseDB.Members.find_one({'_id': topmost_manager})
                    topmost_manager_reports_to = topmost_manager_document.get('reportsTo', None)

                # If topmost_manager_reports_to is not None and not equal to topmost_manager, add it to the managerID list
                if topmost_manager_reports_to is not None and topmost_manager_reports_to != topmost_manager:
                    client.TimesheetDB.EscalationState.update_one({'employeeID': employee_id}, {'$push': {'managerID': topmost_manager_reports_to}})
                    logging.info("[OK] --- Escalation State Updated"+" : EmployeeID : "+ str(employee_id))
            return True
        else:
            # If the connection fails, log an error message
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while checking submitted timesheets")
            return None
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("[ERROR] --- Error checking submitted timesheets: ", type(e).__name__, ":", str(e), " : EmployeeID : "+ str(member['_id']))
        return None

def submitted_timesheets_check():
    try:
        logging.info("[INIT] --- Timesheets Submission Checking Protocol Initiated...")
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Get the current date
            now = datetime.now()
            # Find the start and end of the current week
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)  # Set time to 12AM
            end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)  # Set time to 11:59PM
            # Query the EmployeeSheets collection for all sheets with a startDate or endDate within the current week and a status of submitted or reviewing
            employee_sheets_cursor = client.TimesheetDB.EmployeeSheets.find({
                '$and': [
                    {'startDate': {'$gte': start_of_week, '$lte': end_of_week}},  # startDate is within the current week
                    {'endDate': {'$gte': start_of_week, '$lte': end_of_week}},  # endDate is within the current week
                    {'status': {'$in': ['Submitted', 'Reviewing']}}  # status is submitted or reviewing
                ]
            })
            # Convert the results to a list
            employee_sheets = list(employee_sheets_cursor)
            # Get the list of employees with a submitted or reviewing sheet status
            employees_with_sheets = [sheet['employeeID'] for sheet in employee_sheets]

            # Get the list of employees from the Members collection who are not included in the list of the reviewing and submitted timesheet status
            members_cursor = client.WorkBaseDB.Members.find({
                '_id': {'$nin': employees_with_sheets},
                'name': {'$ne': 'ALL EMPLOYEES'}
            })
            # Convert the results to a list
            members = list(members_cursor)
            # Get the number of timesheets collected for submission
            members_count = len(members) # Get the number of timesheets collected
            logging.info(f"Number of employees hasn't submitted timesheets: {members_count}")  # Log the number of timesheets collected for submission
            logging.info("Initiating Escalation Protocol...")  # Log the start of the process
            success_count = 0  # Variable to keep track of successful thread executions
            # Use a ThreadPoolExecutor to insert documents concurrently
            with ThreadPoolExecutor() as executor:
                results = executor.map(escalation_updation_thread, [(member) for member in members])

            # Return the number of successful thread executions
            for result in results:
                if result is not None:
                    success_count += 1
            if success_count == members_count:
                logging.info(f"[OK] --- All jobs succeeded ({success_count} out of {members_count})")  # Log a success message
            else:
                logging.info(f"[INFO] --- {success_count} out of {members_count} jobs succeeded")  # Log the number of successful jobs

            # Create notifications for the employees and their managers
            create_timesheet_escalation_notifications()
        else:
            logging.error("[ERROR] --- Failed to connect to the MongoDB server while checking submitted timesheets")
        logging.info("[END] --- Timesheets Submission Checking Protocol Completed")  # Log the end of the process

    except Exception as e:
        logging.error("[ERROR] --- Error checking submitted timesheets: ", type(e).__name__, ":", str(e))


# Define a class for the scheduler
class Scheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()  # Initialize the scheduler

    def start(self):
        try:
            logging.info('[EXEC] Starting scheduler...')
            print('Starting scheduler...')
            # Initialize the scheduler
            scheduler = BackgroundScheduler()
            # Add jobs to the scheduler
            # The update_status_timesheets job runs every 15 minutes on Sundays
            logging.info('[EXEC] Adding Jobs...')
            print('Adding Jobs...')
            # scheduler.add_job(create_employee_sheets, 'cron', day_of_week='sun', hour=23, minute="0/15", timezone='America/New_York', args=[])
            # # The distribute_active_timesheets job runs every 15 minutes every day at 15:00 IST
            # scheduler.add_job(distribute_active_timesheets, 'cron', day_of_week='*', hour=15, minute="0/15", timezone='Asia/Kolkata', args=[])
            # # The submit_timesheet_for_review job runs every 15 minutes on Fridays at 20:00 UTC
            # scheduler.add_job(submit_timesheet_for_review, 'cron', day_of_week='fri', hour=20, minute="0/15", timezone='America/New_York', args=[False])
            # # The submit_timesheet_for_review job runs every 15 minutes on Sundays at 20:00 UTC
            # scheduler.add_job(submit_timesheet_for_review, 'cron', day_of_week='sun', hour=20, minute="0/15", timezone='America/New_York', args=[True])
            # Timesheet Submission Check Protocol every friday at 20:00 UTC
            scheduler.add_job(submitted_timesheets_check, 'cron', day_of_week='fri', hour=23, minute=59, second=59, timezone='America/New_York', args=[])
            # Escalated Submission Check Protocol every sunday at 23:00 UTC
            scheduler.add_job(submitted_timesheets_check, 'cron', day_of_week='sun', hour=23, minute=59, second=59, timezone='America/New_York', args=[])
            scheduler.start()  # Start the scheduler
            logging.info("[OK] --- Scheduler started successfully.")
            print("Scheduler started successfully.")
        except Exception as e:
            # If an error occurs, print an error message
            logging.error("[ERROR] --- Error running the scheduler: ",type(e).__name__, ":", str(e))
            print("Error running the scheduler: ",type(e).__name__, ":", str(e))

    def stop(self):
        try:
            # Check if the stop file exists
            if os.path.exists(kill_file_path):
                # If the stop file exists, stop the scheduler and remove the stop file
                logging.info('[EXEC] Stopping scheduler...')
                print('Stopping scheduler...')
                os.remove(kill_file_path)
                self.scheduler.shutdown()
            else:
                # If the stop file does not exist, print a message indicating that the job is running
                logging.info('[EXEC] Running job...')
                print('Running job...')
        except Exception as e:
            # If an error occurs, print an error message
            logging.error("[ERROR] --- Error stopping the scheduler: ",type(e).__name__, ":", str(e))
            print("Error stopping the scheduler: ",type(e).__name__, ":", str(e))
            
# Function to run the scheduler
def main():
    # Create a Scheduler object
    s = Scheduler()
    # Start the scheduler
    s.start()
    while not os.path.exists(kill_file_path):
        time.sleep(2)
    # When you want to stop the scheduler, call the stop method
    s.stop()


# # driver code
# if __name__ == "__main__":
#     main()