from flask import jsonify, Blueprint, request, make_response
from .dbConnection import checkUserValidity
from pymongo import MongoClient

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
    
def checkUserValidity(uid):
    connection_string = f"mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    userProvisioningData = client.sample_employee.UserProvisioningData
    query = userProvisioningData.count_documents({'id': uid}, limit=1)
    
    return  make_response({"message": query != 0}, 200)