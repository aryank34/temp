# This file is used to initialize the system module of the timesheet service
# It imports the required modules and initializes the Flask Blueprint for the system module

from utils import main

if __name__ == "__main__":
    main()
    # client = MongoClient('mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority', server_api=ServerApi('1'), UuidRepresentation="standard")
    # update_status_timesheets(client)
    # distribute_active_timesheets(client)