from flask import Blueprint, request, make_response
from ..loginAuth.tokenAuth import tokenAuth
from .dbConnection import getUsers, addUser, sendDropDown, existingGivenNames, editUser, addUserToAzure,  deleteUser

auth = tokenAuth()

adminView = Blueprint('adminView', __name__)

@adminView.route("/admin/users",methods=['GET'])
@auth.token_auth("/admin/users")
def sendUsers():
    if request.method == 'GET':
        page = request.args.get('page')
        limit = request.args.get('limit')
        return getUsers(int(page), int(limit))
        # return getUsers()


@adminView.route("/admin/users/add", methods = ['GET','POST'])
@auth.token_auth("/admin/users/add")
def insertUser():
    if request.method == 'GET':
        givenNames = existingGivenNames()
        dropDown = sendDropDown()
        return make_response({'givenNames':givenNames, 'dropDown':dropDown}, 200)

    if request.method == 'POST':
        # addUserToAzure(request.json)
        return addUserToAzure(request.json)
        # return addUser(request.json)
    

@adminView.route("/admin/users/edit", methods = ['GET','PUT'])
@auth.token_auth("/admin/users/edit")
def modifyUser():
    #GET method to get the drop downs
    if request.method == 'GET':
        givenNames = existingGivenNames()
        dropDown = sendDropDown()
        return make_response({'givenNames':givenNames, 'dropDown':dropDown}, 200)
    #PUT method
    if request.method == 'PUT':
        return editUser(request.json)
    
@adminView.route("/admin/users/delete", methods = ['DELETE'])
@auth.token_auth("/admin/users/delete")
def removeUser():
    return deleteUser(request.json)