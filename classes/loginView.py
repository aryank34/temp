from flask import jsonify, Blueprint, request, make_response
from .dbConnection import checkUserValidity

loginView = Blueprint('loginView',__name__)

@loginView.route("/login", methods =['GET'])
def checkUser():
    try:
        if request.method == 'GET':
            id = request.json.get('id') #takes uid from frontend
            return checkUserValidity(id) #if correct uid, returns jwt, expiry in 15 minutes
        # if request.method == 'GET':
        #     return make_response('',200)

    except Exception as e:
        error_message = str(e)
        return make_response({'error in loginView': error_message}, 500)
    
