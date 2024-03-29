# Import necessary modules
from flask import Blueprint, jsonify, make_response, request

# Import custom module
from .utils import create_tasks, edit_tasks, fetch_projects, create_projects, create_teams
from ..timesheet.utils import userType
from ..loginAuth.tokenAuth import tokenAuth
auth = tokenAuth()

# Create Flask app instance
project_manager_bp = Blueprint("project_manager_bp", __name__)

# Define route for getting user type
@project_manager_bp.route('/projects', methods=['GET'])
@auth.token_auth("/projects")
def get_projects():
    try:
        # Get the 'uid' from the request's JSON data
        # uid = request.json.get("uid")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Call the userType function from the utils module
        user_type = userType(uuid).json['userType']
        # Call the userType function from the utils module
        fetch_projects_response = fetch_projects(uuid, user_type)

        # Return the response from the userType function
        return fetch_projects_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 500)

# Define route for creating a new project
@project_manager_bp.route('/projects/create', methods=['POST'])
@auth.token_auth("/projects/create")
def create_new_projects():
    try:
        # Get the 'uid' from the request's JSON data
        # uid = request.json.get("uid")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # # Call the userType function from the utils module
        superAdmin = True
        # superAdmin = bool(isSuperAdmin(uuid).json['response'])
        # Get the JSON data sent with the POST request
        payload = request.get_json()
        # Access the 'timesheet' field, which is a nested JSON object
        project_data = payload.get('project')

        if superAdmin:
            fetch_projects_response = create_projects(uuid, project_data)

        # Return the response from the userType function
        return fetch_projects_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 500)

# Define route for creating a new team from project
@project_manager_bp.route('/projects/teams/create', methods=['POST'])
@auth.token_auth("/projects/teams/create")
def create_new_team():
    try:
        # Get the 'uid' from the request's JSON data
        # uid = request.json.get("uid")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # # Call the userType function from the utils module
        superAdmin = True
        # superAdmin = bool(isSuperAdmin(uuid).json['response'])
        # Get the JSON data sent with the POST request
        payload = request.get_json()
        # Access the 'timesheet' field, which is a nested JSON object
        team_data = payload.get('team')

        if superAdmin:
            fetch_teams_response = create_teams(uuid, team_data)

        # Return the response from the userType function
        return fetch_teams_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 500)

# Define route for creating new task
@project_manager_bp.route('/projects/tasks/create', methods=['POST'])
@auth.token_auth("/projects/tasks/create")
def create_new_task():
    try:
        # Get the 'uid' from the request's JSON data
        # uid = request.json.get("uid")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
        # Get the JSON data sent with the POST request
        payload = request.get_json()
        # Access the 'timesheet' field, which is a nested JSON object
        task_data = payload.get('task')

        fetch_tasks_response = create_tasks(uuid, task_data)

        # Return the response from the userType function
        return fetch_tasks_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 500)
    
# Define route for creating new task
@project_manager_bp.route('/projects/tasks/assignment', methods=['POST'])
@auth.token_auth("/projects/tasks/assignment")
def create_new_assignment():
    try:
        # Get the 'uid' from the request's JSON data
        # uid = request.json.get("uid")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
        # Get the JSON data sent with the POST request
        payload = request.get_json()
        # Access the 'timesheet' field, which is a nested JSON object
        task_data = payload.get('task')

        # fetch_tasks_response = create_assignment(uuid, task_data)

        # Return the response from the userType function
        # return fetch_tasks_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 500)

# Define route for creating new task
@project_manager_bp.route('/projects/tasks/assigneeGroup', methods=['POST'])
@auth.token_auth("/projects/tasks/assigneeGroup")
def create_new_assignmentGroup():
    try:
        # Get the 'uid' from the request's JSON data
        # uid = request.json.get("uid")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
        # Get the JSON data sent with the POST request
        payload = request.get_json()
        # Access the 'timesheet' field, which is a nested JSON object
        task_data = payload.get('task')

        # fetch_tasks_response = create_assigneeGroup(uuid, task_data)

        # Return the response from the userType function
        # return fetch_tasks_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 500)

# Define route for creating new task
@project_manager_bp.route('/projects/tasks/edit', methods=['POST'])
@auth.token_auth("/projects/tasks/edit")
def update_task():
    try:
        # Get the 'uid' from the request's JSON data
        # uid = request.json.get("uid")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
        # Get the JSON data sent with the POST request
        payload = request.get_json()
        # Access the 'timesheet' field, which is a nested JSON object
        task_data = payload.get('task')

        fetch_tasks_response = edit_tasks(uuid, task_data)

        # Return the response from the userType function
        return fetch_tasks_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 500)

