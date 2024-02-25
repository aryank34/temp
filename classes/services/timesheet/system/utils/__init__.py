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
log_file_path = os.path.join(parent_dir, 'logfile.log', format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(filename=log_file_path, level=logging.INFO)  # Set the logging configuration    

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
# Define a class for employee sheet objects
class EmployeeSheetObject:
    def __init__(self, projectID: ObjectId, taskID: ObjectId, workDay: dict[str, WorkDay], description: str):  # Initialize the class with project ID, task ID, work day, and description
        self.projectID = projectID  # Assign the project ID
        self.taskID = taskID  # Assign the task ID
        self.workDay = workDay  # Assign the work day
        self.description = description  # Assign the description
    def to_dict(self):  # Convert the object to a dictionary
        return {
            "projectID": self.projectID,
            "taskID": self.taskID,
            "workDay": {day: vars(workDay) for day, workDay in self.workDay.items()},
            "description": self.description
        }
# Define a class for employee sheet instances
class EmployeeSheetInstance:
    def __init__(self, version: int, employeeSheetObject: EmployeeSheetObject):  # Initialize the class with version and employee sheet object
        self.version = version  # Assign the version
        self.employeeSheetObject = employeeSheetObject.to_dict()  # Convert the employee sheet object to a dictionary
    def to_dict(self):  # Convert the instance to a dictionary
        return {
            "version": self.version,
            "employeeSheetObject": self.employeeSheetObject
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
# Define a class for employee sheets
class EmployeeSheet:
    def __init__(self, managerSheetID: ObjectId, employeeID: ObjectId, managerID: ObjectId, startDate: datetime, endDate: datetime, employeeSheetInstances: list[EmployeeSheetInstance]):  # Initialize the class with manager sheet ID, employee ID, manager ID, start date, end date, and employee sheet instances
        self.managerSheetID = managerSheetID  # Assign the manager sheet ID
        self.employeeID = employeeID  # Assign the employee ID
        self.managerID = managerID  # Assign the manager ID
        self.startDate = startDate  # Assign the start date
        self.endDate = endDate  # Assign the end date
        self.employeeSheetInstances = employeeSheetInstances  # Assign the employee sheet instances
        self.status = "Ongoing"  # Initialize the status as "Ongoing"
    def to_dict(self):  # Convert the sheet to a dictionary
        return {
            "managerSheetID": self.managerSheetID,
            "employeeID": self.employeeID,
            "managerID": self.managerID,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "employeeSheetInstances": [vars(employeeSheetInstance) for employeeSheetInstance in self.employeeSheetInstances],
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
# --------------------------------------------------------------------------------------

# Function to check the connection to the MongoDB server
def dbConnectCheck():
    """
    This function creates a new MongoDB client and checks the connection to the MongoDB server.
    It returns the MongoClient instance if the connection is successful, or an error response if the connection fails.
    """
    try:
        uri = mongo_host  # Get the MongoDB host URI
        client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")  # Create a new MongoDB client using the host URI, server API version, and UUID representation
        logging.info('Connection to MongoDB server successful.')
        return client  # Return the client if the connection is successful

    except Exception as e:
        logging.error('Failed to connect to MongoDB server: %s', e)
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
            
            logging.info("Status Update Completed")  # Log a success message
        else:
            # If the connection fails, log an error message
            logging.error("Failed to connect to the MongoDB server while updating status of timesheets")
    except Exception as e:
        # If an error occurs, log the error message
        logging.error("Error updating status of timesheets: %s", e)

# Function to store employee sheets in the database
def store_employee_sheets(data, client):
    try:
        logging.info("Storing employee sheets in the database")
        
        # Create WorkDay object for each day of the week
        workDay = {
            "mon": WorkDay(data["workDay"]["mon"]["work"]),
            "tue": WorkDay(data["workDay"]["tue"]["work"]),
            "wed": WorkDay(data["workDay"]["wed"]["work"]),
            "thu": WorkDay(data["workDay"]["thu"]["work"]),
            "fri": WorkDay(data["workDay"]["fri"]["work"]),
            "sat": WorkDay(data["workDay"]["sat"]["work"]),
            "sun": WorkDay(data["workDay"]["sun"]["work"]),
        }
        logging.info("Created WorkDay object for each day of the week")
        
        # Extract projectID, taskID, and description from the data
        projectID = ObjectId(data["Project"]["projectID"])
        taskID = ObjectId(data["Task"]["taskID"])
        description = data["description"]
        logging.info("Extracted projectID, taskID, and description from the data")
        
        # Create an EmployeeSheetObject with the extracted data and the created WorkDay object
        employeeSheetObject = EmployeeSheetObject(projectID=projectID, taskID=taskID, workDay=workDay, description=description)
        logging.info("Created EmployeeSheetObject")
        
        # Extract version from the data
        version = data["version"]
        logging.info("Extracted version from the data")
        
        # Create an EmployeeSheetInstance with the extracted version and the created EmployeeSheetObject
        employeeSheetInstance = EmployeeSheetInstance(version=version, employeeSheetObject=employeeSheetObject)
        logging.info("Created EmployeeSheetInstance")
        
        # Extract managerSheetID, employeeID, managerID, startDate, and endDate from the data
        managerSheetID = ObjectId(data["managerSheetID"])
        employeeID = ObjectId(data["Employee"]["employeeID"])
        managerID = ObjectId(data["Manager"]["managerID"])
        startDate = data["startDate"]
        endDate = data["endDate"]
        logging.info("Extracted managerSheetID, employeeID, managerID, startDate, and endDate from the data")
        
        # Create an EmployeeSheet with the extracted data and the created EmployeeSheetInstance
        employeeSheet = EmployeeSheet(managerSheetID=managerSheetID, employeeID=employeeID, managerID=managerID, startDate=startDate, endDate=endDate, employeeSheetInstances=[employeeSheetInstance])
        logging.info("Created EmployeeSheet")
        
        # Check if an EmployeeSheet with the same managerSheetID and employeeID already exists in the database
        if (client.TimesheetDB.EmployeeSheets.find_one({"managerSheetID": employeeSheet.managerSheetID, "employeeID": employeeSheet.employeeID}) is None):
            # If not, insert the created EmployeeSheet into the database and log a success message
            result = client.TimesheetDB.EmployeeSheets.insert_one(employeeSheet.to_dict())
            msg_str = "Employee Sheet Created" + ": EmployeeSheetID :" + str(result.inserted_id)
            logging.info("Inserted the created EmployeeSheet into the database")
        else:
            # If an EmployeeSheet with the same managerSheetID and employeeID already exists, check if an EmployeeSheetInstance with the same version already exists
            if (client.TimesheetDB.EmployeeSheets.find_one({"employeeSheetInstances.version": version}) is None):
                # If not, update the existing EmployeeSheet with the created EmployeeSheetInstance and log a success message
                result = client.TimesheetDB.EmployeeSheets.update_one({"employeeID": employeeSheet.employeeID, "managerSheetID": employeeSheet.managerSheetID},
                                                            {"$push": {"employeeSheetInstances": employeeSheetInstance.to_dict()}})
                msg_str = "Employee Sheet updated" + ": EmployeeSheetID :" + str(result.inserted_id)
                logging.info("Updated the existing EmployeeSheet with the created EmployeeSheetInstance")
            else:
                # If an EmployeeSheetInstance with the same version already exists, log a message indicating that the EmployeeSheet already exists
                msg_str = "Employee Sheet already exists"
                logging.info("Employee Sheet already exists")
        
        logging.info(msg_str)  # Log the message
        logging.info("Completed storing employee sheets in the database")
    except Exception as e:
        # If an error occurs, log an error message
        logging.error("Error creating Timesheet Records: %s", e)
        
# Function to distribute active timesheets
def distribute_active_timesheets():
    try:
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Define the pipeline for the aggregation operation on the TimesheetRecords collection
            managerSheet_pipeline = [
                {"$unwind": "$managerSheetsInstances"},
                {"$lookup":{"from": "ManagerSheets",
                            "localField": "managerSheetsInstances.managerSheetsObjects",
                            "foreignField": "_id",
                            "as": "manager"}},
                {"$unwind": "$manager"},
                {"$match":{ "manager.status": "Active"}},
                {"$lookup":{"from": "AssignmentGroup",
                            "localField": "manager.assignGroupID",
                            "foreignField": "_id",
                            "as": "assign"}},
                {"$unwind": "$assign"},
                {"$project":{"managerID": 1,
                            "version": "$managerSheetsInstances.version",
                            "managerSheetID": "$managerSheetsInstances.managerSheetsObjects",
                            "startDate": "$manager.startDate",
                            "endDate": "$manager.endDate",
                            "status": "$manager.status",
                            "projectID": "$assign.projectID",
                            "workDay": "$manager.workDay",
                            "description": "$manager.description",
                            "assignmentID": "$assign.assignmentInstances.assignmentID"}},
                {"$unwind": "$assignmentID"}
            ]

            # Define the pipeline for the aggregation operation on the Assignments collection
            assignment_pipeline = [
                {"$unwind": "$assignedTo"},
                {"$lookup":{"from": "Members",
                            "localField": "assignedTo",
                            "foreignField": "_id",
                            "as": "member"}},
                {"$unwind": "$member"},
                {"$lookup":{"from": "Members",
                            "localField": "assignedBy",
                            "foreignField": "_id",
                            "as": "manager"}},
                {"$unwind": "$manager"},
                {"$lookup":{"from": "Tasks",
                            "localField": "taskID",
                            "foreignField": "_id",
                            "as": "task"}},
                {"$unwind": "$task"},
                {"$lookup":{"from": "Projects",
                            "localField": "projectID",
                            "foreignField": "_id",
                            "as": "project"}},
                {"$unwind": "$project"},
                {"$project":{"_id":0,
                            "assignmentID": "$_id",
                            "Assignment Name": "$name",
                            "Project":{"projectID": "$project._id",
                                        "Project Name": "$project.name"},
                            "Task":{   "taskID": "$task._id",
                                        "Task Name": "$task.name",
                                        "Billable": "$task.billable",
                                        "Task Description": "$task.description",},
                            "Employee":{"employeeID": "$member._id",
                                        "Employee Name": "$member.name"},
                            "Manager":{"managerID": "$manager._id",
                                        "Manager Name": "$manager.name"}}}
            ]

            # Perform the aggregation operations and convert the results to lists
            timesheet_documents = list(client.TimesheetDB.TimesheetRecords.aggregate(managerSheet_pipeline))
            assignment_documents = list(client.WorkBaseDB.Assignments.aggregate(assignment_pipeline))

            # Convert the lists to DataFrames
            timesheet_df = pd.DataFrame(timesheet_documents)
            assignment_df = pd.DataFrame(assignment_documents)

            # Merge the DataFrames on the 'assignmentID' column
            result_df = pd.merge(timesheet_df, assignment_df, on='assignmentID', how='inner')

            # Convert the merged DataFrame to a list of dictionaries
            result_documents = result_df.to_dict(orient='records')

            # For each dictionary in the list, extract a subset of the key-value pairs and store the resulting dictionary in the database
            for i in range(len(result_documents)):
                subset_dict = {key: result_documents[i][key] for key in ['managerSheetID', 'startDate', 'endDate', 'status', 'version', 'workDay', 'description', 'Project', 'Task', 'Employee', 'Manager'] if key in result_documents[i]}
                store_employee_sheets(subset_dict, client)

            print("Timesheets distributed")  # Print a success message
        else:
            # If the connection fails, print an error message
            print("Failed to connect to the MongoDB server while distributing timesheets")
    except Exception as e:
        # If an error occurs, print an error message
        print("Error distributing timesheets: ", e)

# Function to submit timesheets for review
def submit_timesheet_for_review(week_check):
    try:
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            if week_check:  # If week_check is True
                timesheets = get_weekend_timesheets()  # Get the timesheets for the weekend
            else:  # If week_check is False
                timesheets = get_default_timesheets()  # Get the default timesheets
            with ThreadPoolExecutor() as executor:  # Create a ThreadPoolExecutor
                # Use the executor to submit the timesheets for review in parallel
                executor.map(submit_timesheet_for_review_thread, [(timesheet) for timesheet in timesheets])
            print("Timesheets submitted for Review")  # Print a success message
        else:
            # If the connection fails, print an error message
            print("Failed to connect to the MongoDB server while timesheet submission")
    except Exception as e:
        # If an error occurs, print an error message
        print("Error submitting timesheets for review: ", e)

# Function to submit timesheets for review at a thread
def submit_timesheet_for_review_thread(timesheet):
    try:
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            last_instance = timesheet["employeeSheetInstances"][-1]  # Get the last instance of the timesheet

            # Create a new ManagerSheetReview document with the status set to "Review" and the employeeSheetID set to the ID of the timesheet
            managerSheetReview = ManagerSheetReview(status="Review", employeeSheetID=timesheet["_id"])
            newManagerSheetReview = client.TimesheetDB.ManagerSheets.insert_one(managerSheetReview.to_dict())  # Insert the new ManagerSheetReview document into the database
            
            # Add the new ManagerSheetReview document to the TimesheetRecords collection
            client.TimesheetDB.TimesheetRecords.update_one(
                {"managerID": timesheet['managerID']},
                {"$push": {"managerSheetsInstances": {
                    "managerSheetsObjects": newManagerSheetReview.inserted_id,
                    "lastUpdateDate": datetime.now(),
                    "version": last_instance["version"]
                }}}
            )

            # Update the status of the ManagerSheet document to "Draft"
            client.TimesheetDB.ManagerSheets.update_one({"_id": timesheet["managerSheetID"]}, {"$set": {"status": "Draft"}})

            # Update the status of the EmployeeSheet document to "Reviewing" and set the managerSheetID to the ID of the new ManagerSheetReview document
            client.TimesheetDB.EmployeeSheets.update_one({"_id": timesheet["_id"]}, {"$set": {"status": "Reviewing", "managerSheetID": newManagerSheetReview.inserted_id}})
        else:
            # If the connection fails, print an error message
            print("Failed to connect to the MongoDB server while timesheet submission at a thread")
    except Exception as e:
        # If an error occurs, print an error message
        print("Error submitting timesheets for review at a thread: ", e)

# Function to get default timesheets
def get_default_timesheets():
    try:
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Find all EmployeeSheets documents where the status is "Submitted" and both Saturday and Sunday are not work days
            default_timesheets = list(client.TimesheetDB.EmployeeSheets.find({"status": "Ongoing", 
                                                                            "$and": [{"employeeSheetInstances": {"$elemMatch": {"employeeSheetObject.workDay.sat.work": False}}},
                                                                                    {"employeeSheetInstances": {"$elemMatch": {"employeeSheetObject.workDay.sun.work": False}}}]})
            )
            return default_timesheets  # Return the found documents
        else:
            # If the connection fails, print an error message
            print("Failed to connect to the MongoDB server while getting default timesheets")
    except Exception as e:
        # If an error occurs, print an error message
        print("Error getting default timesheets: ", e)

# Function to get weekend timesheets
def get_weekend_timesheets():
    try:        
        client = dbConnectCheck()  # Check the database connection
        if isinstance(client, MongoClient):  # If the connection is successful
            # Find all EmployeeSheets documents where the status is "Submitted" and either Saturday or Sunday is a work day
            weekend_timesheets = list(client.TimesheetDB.EmployeeSheets.find({"status": "Ongoing", 
                                                                            "$or": [
                                                                                {"employeeSheetInstances": {"$elemMatch": {"employeeSheetObject.workDay.sat.work": True}}},
                                                                                {"employeeSheetInstances": {"$elemMatch": {"employeeSheetObject.workDay.sun.work": True}}}]})
            )
            return weekend_timesheets  # Return the found documents
        else:
            # If the connection fails, print an error message
            print("Failed to connect to the MongoDB server while getting weekend timesheets")
    except Exception as e:
        # If an error occurs, print an error message
        print("Error getting weekend timesheets: ", e)

# Define a class for the scheduler
class Scheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()  # Initialize the scheduler

    def start(self):
        try:
            # Initialize the scheduler
            scheduler = BackgroundScheduler()
            # Add jobs to the scheduler
            # The update_status_timesheets job runs every 15 minutes on Sundays
            scheduler.add_job(update_status_timesheets, 'cron', day_of_week='sun', hour=0, minute="0/15", timezone='America/New_York', args=[])
            # The distribute_active_timesheets job runs every 15 minutes every day at 15:00 IST
            scheduler.add_job(distribute_active_timesheets, 'cron', day_of_week='*', hour=15, minute="0/15", timezone='Asia/Kolkata', args=[])
            # The submit_timesheet_for_review job runs every 15 minutes on Fridays at 20:00 UTC
            scheduler.add_job(submit_timesheet_for_review, 'cron', day_of_week='fri', hour=20, minute="0/15", timezone='America/New_York', args=[False])
            # The submit_timesheet_for_review job runs every 15 minutes on Sundays at 20:00 UTC
            scheduler.add_job(submit_timesheet_for_review, 'cron', day_of_week='sun', hour=20, minute="0/15", timezone='America/New_York', args=[True])
            scheduler.start()  # Start the scheduler
        except Exception as e:
            # If an error occurs, print an error message
            print("Error running the scheduler: ", e)

    def stop(self):
        # Check if the stop file exists
        if os.path.exists(kill_file_path):
            # If the stop file exists, stop the scheduler and remove the stop file
            print('Stopping scheduler...')
            os.remove(kill_file_path)
            self.scheduler.shutdown()
        else:
            # If the stop file does not exist, print a message indicating that the job is running
            print('Running job...')

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


# driver code
if __name__ == "__main__":
    
    main()