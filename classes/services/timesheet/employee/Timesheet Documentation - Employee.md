# Timesheet Module Documentation for Employee Role

---

<table>
<tr><td><b><small>Author</small></b></td><td><small><i>Manimit Haldar</i></small></td></tr>
<tr><td><b><small>Role</small></b></td><td><small><i>Intern</i></small></td></tr>
<tr><td><b><small>Email</small></b></td><td><small><i>manimit@encryptionconsulting.com</i></small></td></tr>
<tr><td><b><small>Date</small></b></td><td><small><i>2024-02-23</i></small></td></tr>
</table>

---

This documentation provides an overview of the timesheet module for the employee role. The module includes the following functions:

## Section 1: Retrieving Timesheets
### 1.1 `get_timesheets_for_employee(client, employee_id)`
This function retrieves all timesheets for a specific employee from the database. It takes an instance of MongoClient and the employee ID as input and returns a JSON response containing the timesheets or an error message.

**Example:**

```python
client = MongoClient('mongodb://localhost:27017/')
employee_id = '1234567890'
get_timesheets_for_employee(client, employee_id)
```

### 1.2 `fetch_timesheets(employee_uuid)`
This function fetches all timesheets (or draft timesheets) for an employee. It takes an employee ID as input and returns a JSON response containing the timesheets or an error message.

**Example:**

```python
employee_uuid = '1234567890'
fetch_timesheets(employee_uuid)
```

## Section 2:  Editing Timesheets
### 2.1 `edit_timesheet(employee_uuid, timesheet)`
This function edits an existing timesheet for an employee. It takes the employee ID and timesheet data as input and returns a JSON response containing the updated timesheet or an error message.

Example:

```python
employee_uuid = '1234567890'
timesheet = {
  "employeeSheetID": "60d21b126d8d15b6c0b77a8c",
  "workDay": {
    "mon": {"work": true, "hour": 8, "comment": "Worked on project X"},
    "tue": {"work": true, "hour": 8, "comment": "Worked on project Y"},
    "wed": {"work": true, "hour": 8, "comment": "Worked on project Z"},
    "thu": {"work": true, "hour": 8, "comment": "Worked on project X"},
    "fri": {"work": true, "hour": 8, "comment": "Worked on project Y"},
    "sat": {"work": false, "hour": 0, "comment": ""},
    "sun": {"work": false, "hour": 0, "comment": ""},
  }
}
edit_timesheet(employee_uuid, timesheet)
```

Each function performs various checks to ensure the validity of the input data and the successful execution of the operation. If an error occurs during the execution of a function, it returns a JSON response containing an error message.

---