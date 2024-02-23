# Timesheet Management System

---

<table>
<tr><td><b><small>Author</small></b></td><td><small><i>Manimit Haldar</i></small></td></tr>
<tr><td><b><small>Role</small></b></td><td><small><i>Intern</i></small></td></tr>
<tr><td><b><small>Email</small></b></td><td><small><i>manimit@encryptionconsulting.com</i></small></td></tr>
<tr><td><b><small>Date</small></b></td><td><small><i>2024-02-23</i></small></td></tr>
</table>

---


This script is a part of a timesheet management system. It uses MongoDB as its database and the APScheduler library to schedule tasks.

## Classes

- `ManagerSheetsInstance`: This class likely represents a specific instance of a timesheet for a manager. It might contain properties like the manager's ID, the timesheet's start and end dates, and a list of time entries.
- `TimesheetRecord`: This class likely represents a single record in a timesheet. It might contain properties like the date of the work, the number of hours worked, and the type of work done.
- `WorkDay`: This class likely represents a single workday. It might contain properties like the date, the start and end times of work, and any breaks taken.
- `ManagerSheetsAssign`: This class likely represents an assignment of a timesheet to a manager. It might contain properties like the manager's ID, the timesheet ID, and the assignment date.
- `EmployeeSheetObject`: This class likely represents a timesheet for an employee. It might contain properties like the employee's ID, the timesheet's start and end dates, and a list of time entries.
- `EmployeeSheetInstance`: This class likely represents a specific instance of a timesheet for an employee. It might contain properties like the employee's ID, the timesheet's start and end dates, and a list of time entries.
- `ManagerSheetReview`: This class likely represents a review of a timesheet by a manager. It might contain properties like the manager's ID, the timesheet ID, the review date, and the manager's comments.
- `EmployeeSheet`: This class likely represents a timesheet for an employee. It might contain properties like the employee's ID, the timesheet's start and end dates, and a list of time entries.
- `AssignmentInstance`: This class likely represents a specific instance of an assignment. It might contain properties like the assignment ID, the assignee's ID, the assigner's ID, and the assignment date.
- `AssignmentGroup`: This class likely represents a group of assignments. It might contain properties like a list of assignment instances and a group ID.

## Functions

- `dbConnectCheck()`: This function is responsible for establishing a connection with the MongoDB server. It creates a new MongoDB client and checks the connection status. If the connection is successful, it returns the client object; otherwise, it might throw an error or return a failure status.
- `get_next_week()`: This function calculates and returns the date of the next Monday at midnight. This could be useful in a timesheet system for scheduling tasks or generating timesheets for the upcoming week.
- `update_status_timesheets()`: This function updates the status of upcoming timesheets to active. It might be used when a new week starts and the timesheets for that week need to be activated.
- `store_employee_sheets(data, client)`: This function takes employee timesheet data and a MongoDB client as arguments. It stores the employee timesheet data in the MongoDB database using the provided client.
- `distribute_active_timesheets()`: This function distributes active timesheets. The exact distribution mechanism might depend on the specifics of the system, but it could involve sending the timesheets to employees or managers via email or a web interface.
- `submit_timesheet_for_review(week_check)`: This function submits timesheets for review. The week_check parameter might be a date or week number indicating which week's timesheets should be submitted for review.
- `submit_timesheet_for_review_thread(timesheet)`: This function is used by submit_timesheet_for_review to submit timesheets for review in parallel. It takes a single timesheet as an argument and submits it for review. By running this function in multiple threads, the system can submit multiple timesheets for review simultaneously.
- `get_default_timesheets()`: This function retrieves default timesheets from the MongoDB database. These might be template timesheets that are used as a starting point when creating new timesheets.
- `get_weekend_timesheets()`: This function retrieves timesheets for the weekend from the MongoDB database. This could be useful in a system where weekend work is tracked separately from weekday work.

## Scheduler

The `Scheduler` class is used to schedule tasks. It uses the APScheduler library to schedule tasks at specific times.

- `start()`: Starts the scheduler and adds jobs to it.
- `stop()`: Stops the scheduler.

## Main Function

The `main` function creates an instance of the `Scheduler` class, starts it, and then stops it.
