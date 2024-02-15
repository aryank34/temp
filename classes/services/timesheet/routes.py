# Import necessary modules
from flask import Blueprint, jsonify, make_response, request

# Import custom module
from .utils import userType

from ..loginAuth.tokenAuth import tokenAuth
auth = tokenAuth()

# Create Flask app instance
timesheet_bp = Blueprint("timesheet_bp", __name__)

# Define route for getting user type
@timesheet_bp.route('/timesheet', methods=['GET'])
@auth.token_auth("/timesheet")
def get_user_type():
    try:
        # Get the 'uid' from the request's JSON data
        # uid = request.json.get("uid")
        uuid = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']

        # Call the userType function from the utils module
        user_type_response = userType(uuid)

        # Return the response from the userType function
        return user_type_response

    except Exception as e:
        # Handle any exceptions and return an error response
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 500)

