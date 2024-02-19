# api/services/timesheet/manager/routes.py
from flask import Blueprint, jsonify, request

# Import custom module
from .utils import create_timesheet, fetch_timesheets

from ...loginAuth.tokenAuth import tokenAuth
auth = tokenAuth()

manager_timesheet_bp = Blueprint("manager_timesheet", __name__)

@manager_timesheet_bp.route("/timesheet/manager/assign", methods=["GET"])
@auth.token_auth("/timesheet/manager/assign")
def manage_timesheet():
    try:
        # Get the 'uid' from the request's JSON data
        # uuid = request.json.get("id")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Call the fetch_managerTimesheets function from the utils module
        managerTimesheets_response = fetch_timesheets(uuid, status="Assign")

        # Return the response from the userType function
        return managerTimesheets_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

@manager_timesheet_bp.route("/timesheet/manager/review", methods=["GET"])
@auth.token_auth("/timesheet/manager/review")
def review_timesheet():
    try:
        # Get the 'uid' from the request's JSON data
        # uuid = request.json.get("id")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Call the fetch_managerTimesheets function from the utils module
        managerTimesheets_response = fetch_timesheets(uuid, status="Review")

        # Return the response from the userType function
        return managerTimesheets_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

@manager_timesheet_bp.route("/timesheet/manager/create", methods=["POST"])
@auth.token_auth("/timesheet/manager/create")
def create_new_timesheet():
    try:
        # Get the JSON data sent with the POST request
        payload = request.get_json()

        # Access the 'uid' field
        # uuid = payload.get('id')
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Access the 'timesheet' field, which is a nested JSON object
        timesheet = payload.get('timesheet')

        # Call the create_timesheet function from the utils module
        create_timesheet_response = create_timesheet(uuid, timesheet)

        # Return the response from the userType function
        return create_timesheet_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

@manager_timesheet_bp.route("/timesheet/manager/draft", methods=["GET"])
@auth.token_auth("/timesheet/manager/draft")
def get_draft_timesheet():
    try:
        # Get the 'uid' from the request's JSON data
        # uuid = request.json.get("id")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Call the fetch_managerTimesheets function from the utils module
        managerTimesheets_response = fetch_timesheets(uuid, status="Draft")

        # Return the response from the userType function
        return managerTimesheets_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500


