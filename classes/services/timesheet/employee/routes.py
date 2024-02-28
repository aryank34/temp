# api/services/timesheet/employee/routes.py
from flask import Blueprint, jsonify, request

# from ....tokenAuth import tokenAuth

from ...loginAuth.tokenAuth import tokenAuth
auth = tokenAuth()

from .utils import fetch_employee_project_tasks, fetch_timesheets, edit_timesheet

# auth = tokenAuth()

employee_timesheet_bp = Blueprint("employee_timesheet", __name__)

@employee_timesheet_bp.route("/timesheet/employee/active", methods=["GET"])
@auth.token_auth("/timesheet/employee/active")
# @auth.token_auth("/timesheet/employee/active")
def manage_timesheet():
    try:
        # Get the 'uuid' from the request's JSON data
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
        # uuid = request.json.get("id")

        # Call the fetch_employeeTimesheets function from the utils module
        employeeTimesheets_response = fetch_timesheets(uuid)

        # Return the response from the userType function
        return employeeTimesheets_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

@employee_timesheet_bp.route("/timesheet/employee/", methods=["GET"])
@auth.token_auth("/timesheet/employee/")
# @auth.token_auth("/timesheet/employee/active")
def fetch_data():
    try:
        # Get the 'uuid' from the request's JSON data
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
        # uuid = request.json.get("id")

        # Call the fetch_employeeTimesheets function from the utils module
        employeeProjectsTasks_response = fetch_employee_project_tasks(uuid)

        # Return the response from the userType function
        return employeeProjectsTasks_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500



@employee_timesheet_bp.route("/timesheet/employee/submit", methods=["POST"])
@auth.token_auth("/timesheet/employee/submit")
def edit_existing_timesheet():
    try:
        # Get the JSON data sent with the POST request
        payload = request.get_json()

        # Access the 'uid' field
        # uuid = payload.get('id')
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Access the 'timesheet' field, which is a nested JSON object
        timesheet = payload.get('timesheet')

        # Call the create_timesheet function from the utils module
        edit_timesheet_response = edit_timesheet(uuid, timesheet)

        # Return the response from the userType function
        return edit_timesheet_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500
