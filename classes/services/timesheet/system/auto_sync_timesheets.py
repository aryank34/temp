# # This file is used to initialize the system module of the timesheet service
# # It imports the required modules and initializes the Flask Blueprint for the system module
from utils import main

# # This is a standard boilerplate in Python that allows or prevents parts of code from being run when the modules are imported.
if __name__ == "__main__":
    # When your script is run by passing it as a command to the Python interpreter,
    # __name__ is set as __main__, so this part of the code will run.
    # with app.app_context():
    main()  # Call the main function