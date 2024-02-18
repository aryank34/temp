from flask import jsonify, Blueprint, request, make_response
from ..EmployeeData.dbConnection import checkUserValidity
from flask_jwt_extended import jwt_required, get_jwt

loginView = Blueprint('loginView',__name__)

@loginView.route("/login", methods =['GET',"POST"])
def checkUser():
    try:
        if request.method == 'POST':
            id = request.json.get('id') #takes uid from frontend
            return checkUserValidity(id) #if correct uid, returns jwt, expiry in 15 minutes
        # if request.method == 'GET':
        #     return make_response('',200)

    except Exception as e:
        error_message = str(e)
        return make_response({'error in loginView': error_message}, 500)

    
