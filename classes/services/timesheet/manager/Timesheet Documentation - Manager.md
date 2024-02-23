# Timesheet Module Documentation for Manager Role

---

<table>
<tr><td><b><small>Author</small></b></td><td><small><i>Manimit Haldar</i></small></td></tr>
<tr><td><b><small>Role</small></b></td><td><small><i>Intern</i></small></td></tr>
<tr><td><b><small>Email</small></b></td><td><small><i>manimit@encryptionconsulting.com</i></small></td></tr>
<tr><td><b><small>Date</small></b></td><td><small><i>2024-02-23</i></small></td></tr>
</table>

---

This documentation provides an overview of the timesheet module for the manager role. The module includes the following functions:

## Section 1: Retrieving Timesheets
### 1.1 `get_timesheets_for_manager(client, manager_id)`
This function retrieves all timesheets for a specific manager from the database. It takes an instance of MongoClient and the manager ID as input and returns a JSON response containing the timesheets or an error message.

**Example:**

```python
client = MongoClient('mongodb://localhost:27017/')
manager_id = '1234567890'
get_timesheets_for_manager(client, manager_id)
```

## Section 2: Submitting and Approving Timesheets
### 2.1 `approve_timesheet(manager_uuid, timesheet_id)`
This function submits a specific timesheet for a manager. It takes the manager ID and timesheet ID as input and returns a JSON response containing a success message or an error message.

Example:

```python
manager_uuid = '1234567890'
timesheet = {
    "employeeSheetID": "60d21b126d8d15b6c0b77a8c",
    "managerSheetID": "60d21b126d8dh4h6c0b77a8c"
}
submit_timesheet(manager_uuid, timesheet)
```

## Section 3: Editing, Deleting, and Creating Timesheets
### 3.1 `edit_timesheet(manager_uuid, timesheet)`
This function edits an existing timesheet for a manager. It takes the manager ID and timesheet data as input and returns a JSON response containing the updated timesheet or an error message.

Example:

```python
manager_uuid = '1234567890'
timesheet = {
  "managerSheetID": "60d21b126d8d15b6c0b77a8c",
  "assignGroupID": "60d21b126d8d15b6c0b77a8d",
  "projectID": "60d21b126d8d15b6c0b77a8e",
  "startDate": "2022-01-01 00:00:00",
  "endDate": "2022-01-31 23:59:59",
  "workDay": {
    "mon": true,
    "tue": true,
    "wed": true,
    "thu": true,
    "fri": true,
    "sat": false,
    "sun": false,
  },
  "description": "Manager Notes",
}
edit_timesheet(manager_uuid, timesheet)
```

### 3.2 `delete_timesheet(manager_uuid, timesheet)`
This function deletes an existing timesheet for a manager. It takes the manager ID and timesheet data as input and returns a JSON response containing a success message or an error message.

Example:

```python
manager_uuid = '1234567890'
timesheet = {
  "managerSheetID": "60d21b126d8d15b6c0b77a8c"
}
delete_timesheet(manager_uuid, timesheet)
```

### 3.3 `create_timesheet(manager_uuid, timesheet)`
This function creates a new timesheet for a manager. It takes the manager ID and timesheet data as input and returns a JSON response containing the new timesheet or an error message.

Example:

```python
manager_uuid = '1234567890'
timesheet = {
  "assignGroupID": "60d21b126d8d15b6c0b77a8d",
  "projectID": "60d21b126d8d15b6c0b77a8e",
  "startDate": "2022-01-01 00:00:00",
  "endDate": "2022-01-31 23:59:59",
  "action": "Draft",
  "workDay": {
    "mon": true,
    "tue": true,
    "wed": true,
    "thu": true,
    "fri": true,
    "sat": false,
    "sun": false,
  },
  "description": "Manager Notes",
}
create_timesheet(manager_uuid, timesheet)
```

## Section 4: Fetching Manager Data
### 4.1 `get_workData(client, manager_id)`
This function retrieves all assignments, projects, tasks, and employees for a manager from the database. It takes an instance of MongoClient and the manager ID as input and returns a JSON response containing the manager data or an error message.

Example:

```python
client = MongoClient('mongodb://localhost:27017/')
manager_id = '1234567890'
get_workData(client, manager_id)
```

### 4.2 `fetch_managerData(manager_uuid)`
This function fetches the manager data for assignments, projects, tasks, employees used for timesheet assignments. It takes a manager ID as input and returns a JSON response containing the manager data or an error message.

Example:

```python
manager_uuid = '1234567890'
fetch_managerData(manager_uuid)
```

Each function performs various checks to ensure the validity of the input data and the successful execution of the operation. If an error occurs during the execution of a function, it returns a JSON response containing an error message.

---
