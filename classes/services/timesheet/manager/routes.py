# api/services/timesheet/manager/routes.py
from flask import Blueprint, jsonify, make_response, request

# Import custom module
from .utils import edit_timesheet, create_timesheet, fetch_review_timesheets, fetch_submitted_timesheets, fetch_timesheets, fetch_managerData, return_timesheet, approve_timesheet, delete_timesheet

from ...loginAuth.tokenAuth import tokenAuth
auth = tokenAuth()

manager_timesheet_bp = Blueprint("manager_timesheet", __name__)

@manager_timesheet_bp.route("/timesheet/manager", methods=["GET"])
@auth.token_auth("/timesheet/manager")
def get_manager_data():
    try:
        # Get the 'uid' from the request's JSON data
        # uuid = request.json.get("id")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Call the fetch_managerTimesheets function from the utils module
        managerData_response = fetch_managerData(uuid)

        # Return the response from the userType function
        return managerData_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

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

@manager_timesheet_bp.route("/timesheet/manager/submitted", methods=["GET"])
@auth.token_auth("/timesheet/manager/submitted")
def submitted_history_timesheet():
    try:
        # Get the 'uid' from the request's JSON data
        # uuid = request.json.get("id")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Call the fetch_managerTimesheets function from the utils module
        managerTimesheets_response = fetch_submitted_timesheets(uuid)

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
        managerTimesheets_response = fetch_review_timesheets(uuid)

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

@manager_timesheet_bp.route("/timesheet/manager/delete", methods=["DELETE"])
@auth.token_auth("/timesheet/manager/delete")
def del_timesheet():
    try:
        # Get the JSON data sent with the POST request
        payload = request.get_json()

        # Access the 'uid' field
        # uuid = payload.get('id')
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Access the 'timesheet' field, which is a nested JSON object
        timesheet = payload.get('timesheet')

        # Call the create_timesheet function from the utils module
        delete_timesheet_response = delete_timesheet(uuid, timesheet)

        # Return the response from the userType function
        return delete_timesheet_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500
    
@manager_timesheet_bp.route("/timesheet/manager/edit", methods=["POST"])
@auth.token_auth("/timesheet/manager/edit")
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

@manager_timesheet_bp.route("/timesheet/manager/return", methods=["POST"])
@auth.token_auth("/timesheet/manager/return")
def return_review_timesheet():
    try:
        # Get the JSON data sent with the POST request
        payload = request.get_json()

        # Access the 'uid' field
        # uuid = payload.get('id')
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Access the 'timesheet' field, which is a nested JSON object
        timesheet = payload.get('timesheet')

        # Call the create_timesheet function from the utils module
        return_timesheet_response = return_timesheet(uuid, timesheet)

        # Return the response from the userType function
        return return_timesheet_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return jsonify({'error': error_message}), 500

@manager_timesheet_bp.route("/timesheet/manager/approve", methods=["POST"])
@auth.token_auth("/timesheet/manager/approve")
def approve_review_timesheet():
    try:
        # Get the JSON data sent with the POST request
        payload = request.get_json()

        # Access the 'uid' field
        # uuid = payload.get('id')
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Access the 'timesheet' field, which is a nested JSON object
        timesheet = payload.get('timesheet')
        # return make_response(jsonify(timesheet), 200)

        # Call the create_timesheet function from the utils module
        approve_timesheet_response = approve_timesheet(uuid, timesheet)

        # Return the response from the userType function
        return approve_timesheet_response

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


