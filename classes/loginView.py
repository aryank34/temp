from flask import jsonify, Blueprint, request, make_response
from .dbConnection import checkUserValidity

loginView = Blueprint('loginView',__name__)

@loginView.route("/login", methods =['GET','POST'])
def checkUser():
    try:
        if request.method == 'POST':
            uid = request.json.get('uid')
            return checkUserValidity(uid)
        if request.method == 'GET':
            return make_response('',200)

    except Exception as e:
        error_message = str(e)
        return make_response({'error in loginView': error_message}, 500)