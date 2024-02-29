# api/services/timesheet/employee/routes.py
from flask import Blueprint, jsonify, request
from flask_cors import CORS
# from ....tokenAuth import tokenAuth

from ...loginAuth.tokenAuth import tokenAuth
auth = tokenAuth()

from .utils import employee_timesheet_operation, fetch_draft_timesheets, fetch_employee_project_tasks, fetch_submitted_timesheets, fetch_timesheets, edit_timesheet, fetch_total_timesheets

# auth = tokenAuth()

employee_timesheet_bp = Blueprint("employee_timesheet", __name__)

@employee_timesheet_bp.route("/timesheet/employee/active", methods=["GET"])
@auth.token_auth("/timesheet/employee/active")
def manage_timesheet():
    if request.method == "GET":
        try:
            # Get the 'uuid' from the request's JSON data
            uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
            # uuid = request.json.get("id")

            # Call the fetch_employeeTimesheets function from the utils module
            employeeTimesheets_response = fetch_timesheets(uuid)
            # employeeTimesheets_response = fetch_total_timesheets(uuid,['Ongoing', 'Returned'])

            # Return the response from the userType function
            return employeeTimesheets_response

        except Exception as e:
            # Handle any exceptions and return an error response
            error_message = str(e)
            return jsonify({'error': error_message}), 500
    

@employee_timesheet_bp.route("/timesheet/employee/draft", methods=["GET"])
@auth.token_auth("/timesheet/employee/draft")
def draft_timesheet():
    if request.method == "GET":
        try:
            # Get the 'uuid' from the request's JSON data
            uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
            # uuid = request.json.get("id")

            # Call the fetch_employeeTimesheets function from the utils module
            employeeTimesheets_response = fetch_draft_timesheets(uuid)
            # employeeTimesheets_response = fetch_total_timesheets(uuid,['Draft'])
            # Return the response from the userType function
            return employeeTimesheets_response

        except Exception as e:
            # Handle any exceptions and return an error response
            error_message = str(e)
            return jsonify({'error': error_message}), 500

@employee_timesheet_bp.route("/timesheet/employee/submitted", methods=["GET"])
@auth.token_auth("/timesheet/employee/submitted")
def submitted_timesheet():
    if request.method == "GET":
        try:
            # Get the 'uuid' from the request's JSON data
            uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
            # uuid = request.json.get("id")

            # Call the fetch_employeeTimesheets function from the utils module
            employeeTimesheets_response = fetch_submitted_timesheets(uuid)
            # employeeTimesheets_response = fetch_total_timesheets(uuid,['Reviewing', 'Submitted'])
            # Return the response from the userType function
            return employeeTimesheets_response

        except Exception as e:
            # Handle any exceptions and return an error response
            error_message = str(e)
            return jsonify({'error': error_message}), 500

@employee_timesheet_bp.route("/timesheet/employee", methods=["GET"])
@auth.token_auth("/timesheet/employee")
def fetch_data():
    if request.method == "GET":
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

# @employee_timesheet_bp.route("/timesheet/employee/save", methods=["POST"])
# @auth.token_auth("/timesheet/employee/save")
# def save_incoming_timesheet():
#     try:
#         # Get the JSON data sent with the POST request
#         payload = request.get_json()

#         # Access the 'uid' field
#         # uuid = payload.get('id')
#         uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

#         # Access the 'timesheet' field, which is a nested JSON object
#         timesheet = payload.get('timesheet')

#         # Call the create_timesheet function from the utils module
#         save_timesheet_response = save_timesheet(uuid, timesheet)

#         # Return the response from the userType function
#         return save_timesheet_response

#     except Exception as e:
#         # Handle any exceptions and return an error response
#         error_message = str(e)
#         return jsonify({'error': error_message}), 500


@employee_timesheet_bp.route("/timesheet/employee/submit", methods=["POST"])
@auth.token_auth("/timesheet/employee/submit")
def edit_existing_timesheet():
    if request.method == "POST":
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

@employee_timesheet_bp.route("/timesheet/employee/action", methods=["POST"])
@auth.token_auth("/timesheet/employee/action")
def operation_on_timesheet():
    if request.method == "POST":
        try:
            # Get the JSON data sent with the POST request
            payload = request.get_json()

            # Access the 'uid' field
            # uuid = payload.get('id')
            uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

            # Access the 'timesheet' field, which is a nested JSON object
            timesheet = payload.get('timesheet')

            # Call the create_timesheet function from the utils module
            edit_timesheet_response = employee_timesheet_operation(uuid, timesheet)

            # Return the response from the userType function
            return edit_timesheet_response

        except Exception as e:
            # Handle any exceptions and return an error response
            error_message = str(e)
        return jsonify({'error': error_message}), 500
