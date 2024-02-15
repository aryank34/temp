# api/timesheet/employee/routes.py
from flask import Blueprint, jsonify, request

# from ....tokenAuth import tokenAuth

from ...loginAuth.tokenAuth import tokenAuth
auth = tokenAuth()

from .utils import fetch_timesheets

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