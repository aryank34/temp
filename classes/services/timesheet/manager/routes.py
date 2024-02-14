# api/timesheet/manager/routes.py
from flask import Blueprint, jsonify, request

# Import custom module
from .utils import create_timesheet, fetch_timesheets

import sys

sys.path.insert(0, "\\classes\\")
import tokenAuth

# from backend.classes.tokenAuth import tokenAuth
auth = tokenAuth.tokenAuth()
#create object of authMongo class

manager_timesheet_bp = Blueprint("manager_timesheet", __name__)

@manager_timesheet_bp.route("/timesheet/manage", methods=["GET"])
@auth.token_auth("/timesheet/manage")
# @auth.token_auth("/timesheet/manage")
def manage_timesheet():
    try:
        # Get the 'uid' from the request's JSON data
        uid = request.json.get("uid")

        # Call the fetch_managerTimesheets function from the utils module
        managerTimesheets_response = fetch_timesheets(uid, status="Manage")

        # Return the response from the userType function
        return managerTimesheets_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

@manager_timesheet_bp.route("/timesheet/create", methods=["POST"])
def create_new_timesheet():
    try:
        # Get the JSON data sent with the POST request
        payload = request.get_json()

        # Access the 'uid' field
        uid = payload.get('uid')

        # Access the 'timesheet' field, which is a nested JSON object
        timesheet = payload.get('timesheet')

        # # Now you can access the fields of the timesheet like this:
        # project_id = timesheet.get('projectID')
        # start_date = timesheet.get('startDate')
        # end_date = timesheet.get('endDate')
        # work_day = timesheet.get('workDay')
        # description = timesheet.get('description')
        # status = timesheet.get('status')
        # assign_group_id = timesheet.get('assignGroupID')

        # Call the create_timesheet function from the utils module
        create_timesheet_response = create_timesheet(uid, timesheet)

        # Return the response from the userType function
        return create_timesheet_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

@manager_timesheet_bp.route("/timesheet/draft", methods=["GET"])
def get_draft_timesheet():
    try:
        # Get the 'uid' from the request's JSON data
        uid = request.json.get("uid")

        # Call the fetch_managerTimesheets function from the utils module
        managerTimesheets_response = fetch_timesheets(uid, status="Draft")

        # Return the response from the userType function
        return managerTimesheets_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

# @manager_timesheet_bp.route("/timesheet/assign", methods=["POST"])
# def assign_timesheet_to_employee():
#     data = request.json
#     result = assign_timesheet(data)
#     return jsonify(result)
