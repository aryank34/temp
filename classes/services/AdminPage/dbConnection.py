from flask import make_response
from pymongo import MongoClient
#to get Object Id from mongodb
from bson.objectid import ObjectId
#load and find the env file
from dotenv import load_dotenv, find_dotenv
import os

from uuid import UUID

from ..EmployeeData.dbConnection import setTotalEmployees

# import requests
# import json
# from azure.identity import ClientSecretCredential
# from azure.graphrbac import GraphRbacManagementClient
# from azure.common.credentials import ServicePrincipalCredentials

import msal
import requests
import json

from pymongo.server_api import ServerApi

# import requests
# import sys
# print(sys.path)

load_dotenv(find_dotenv())
# mongo_password = os.environ.get("MONGO_PWD")
# connection_string = f"mongodb+srv://admin:{mongo_password}@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority"
# client = MongoClient(connection_string, UuidRepresentation="standard")

mongo_host = os.environ.get("MONGO_HOST_prim")
uri = mongo_host
client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")

employeeData = client.EmployeeDB.employeeData

# def getUsers():
def getUsers(page, limit):
    try:
        users = list(employeeData.find({'status':'Active'},{"userType":0,"emp_id":0,"Last_modification":0,"Certificate_Id":0}).skip((page - 1) * limit).limit(limit))
        # users = list(employeeData.find({'status':'Active'},{"userType":0,"emp_id":0,"Last_modification":0,"Certificate_Id":0}))
        # print(users)
        data_obj={}
        for index,user in enumerate(users, start=1):
            if 'file_id' in user:
                obj = list(user['file_id'])
                # print(obj)
                for file in obj:
                    user['file_id'][file] = 'True'
            else:
                user['file_id'] = 'No File'
            if 'profile_picture_id' in user:
                user['profile_picture_id'] = 'True'
            else:
                user['profile_picture_id'] = 'No File'
            user['_id'] = str(user['_id'])
            user['id'] = str(user['id'])
            user['ReportingToID'] = str(user['ReportingToID'])
            data_obj[index] = user
        # print(data_obj)
        
        return make_response({"message":data_obj}, 200)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
    
def sendDropDown():
    try:
        #drop downs - managers givenName, emailid list(include everyone except employee), roles(Employee, marketing...)
        # query = {"$nin":['Employee']}
        query = {"$in":['SuperAdmin','Manager']}
        higherRoleUsers = list(employeeData.find({"$and":[{'status':'Active'},{'Role.role_name':query}]},{'_id':1, 'givenName':1,'mail':1}))
        # print(higherRoleUsers)
        data_obj={}
        for index,user in enumerate(higherRoleUsers, start=1):
            data_obj[index] = user
            data_obj[index]['_id'] = str(user['_id'])
            data_obj[index]['givenName'] = user['givenName']
            data_obj[index]['mail'] = user['mail']
        return data_obj
    except Exception as e:
        return str(e)
    
def existingGivenNames():
    try:
        existingGivenNames = list(employeeData.find({},{'_id':0,'givenName':1}))
        # print(existingGivenNames)
        existing_names = []
        for name in existingGivenNames:
            existing_names.append(name['givenName'])
        existing_names = list(set(existing_names))
        
        return existing_names
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)

#add users in microsoft azure and then it will automatically add it in mongodb otherwise the
#user wont be able to log in
    
def addUserToAzure(data):
    try:
        # print(data)
        tenant_id=os.environ.get("AZURE_TENANT_ID")
        # print(tenant_id)
        client_id=os.environ.get("AZURE_CLIENT_ID")
        # print(client_id)
        client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        # print(client_secret)
        # print('here')

        # client_id = "appId"
        # client_secret= "secret"
        # tenant_id = "tenantId"
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        # print('here')
        scopes = ['https://graph.microsoft.com/.default']
        # print('here')
        app = msal.ConfidentialClientApplication(client_id, client_secret, authority=authority)
        # print('here')
        result = app.acquire_token_for_client(scopes)
        # print('here')
        # print(result)
        access_token = result['access_token']
        # print(access_token)
        # print('here')
        headers = {'Authorization': 'Bearer ' + access_token}
        # print('here')
        url = 'https://graph.microsoft.com/v1.0/users'
        # print('here')
        user = {
            "accountEnabled": True,
            "displayName": f"{data['givenName']}",
            "mailNickname": f"{data['givenName']}",
            "userPrincipalName": f"{data['mail']}",
            "passwordProfile": {
                "forceChangePasswordNextSignIn": True,
                "password": "@NikePuma007@"
            },
            "mail":f"{data['mail']}",
            "givenName":f"{data['FirstName']}",
            "surname":f"{data['LastName']}",
            "usageLocation":f"{data['usageLocation']}"
        }
        # print('here')

        response = requests.post(url, headers=headers, json=user)
        # print('here')
        # print(response)
        if response.status_code == 201:
            print('User created successfully!')
            # print(json.loads(response.content)["id"])
            data["id"] = str(json.loads(response.content)["id"])
            if addUser(data):
                return make_response({"message":"User Added"}, 201)
            else:
                return make_response({"ERROR":'Failed to add user in mongodb'}, 500)
        else:
            return make_response({"ERROR creating user on azure:":response.text}, 500)
            # print('Error creating user:', response.text)
        # print('true')
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
        # print(str(e))
    
def addUser(data):
    try:
        #number of active employees is set
        setTotalEmployees()

        #add another employee
        data['id'] = UUID(data['id'])

        #get the last emp_id
        last_document_emp_iD = employeeData.find_one(sort=[("_id", -1)], limit=1)['emp_id']
        # print(last_document_emp_iD)
        #extract number
        num = int(last_document_emp_iD[2:]) #get the string from index 2 and convert to int
        #give new ID
        new_emp_id = f"ID{num+1}"
        # print(new_emp_id)
        data['emp_id'] = new_emp_id

        #check givenName already should not exist or send it in drop down GET request

        #save certificates name & id as an array

        #ReportingToId should be stored as ObjectID

        #before adding the object check for Role, role_name and role_id array
        
        # print(data)
        data['Certificate_Name'] = []
        data['Certificate_Id'] = []
        data['Emergency_Contact_Name'] = ""
        data['Emergency_Contact_Number'] = ""
        data['Emergency_Relation'] = ""
        ReportingToId = ObjectId(employeeData.find_one({'givenName':data['ReportingTo']},{"_id":1})['_id'])
        data['ReportingToID'] = ReportingToId
        Role = {"role_name":data['role_name'],"role_id":data['role_id']}
        data['Role'] = Role
        data.pop('role_name')
        data.pop('role_id')
        
        response = employeeData.insert_one(data)
        if response.inserted_id:
            return True
        else:
            return False
    except Exception as e:
        return str(e)

#edit the mongodb and azure database both, directly from admin but requires approval when employee edits something
def editUser(data):
    try:
        id = UUID(data['id'])
        ReportingToId = ObjectId(employeeData.find_one({'givenName':data['ReportingTo']},{"_id":1})['_id'])
        data['ReportingToID'] = ReportingToId
        Role = {"role_name":data['role_name'],"role_id":data['role_id']}
        data['Role'] = Role
        data.pop('id')
        data.pop('role_name')
        data.pop('role_id')
        # print(data)
        response = employeeData.update_one({'id':id},{"$set":data})
        if response.matched_count == 1:
            #number of active employees is set
            setTotalEmployees()
            if editUserToAzure(id, data):
                return make_response({"message":"Data Edited"}, 200)
            else:
                return make_response({"ERROR":'Failed to update user on Azure'}, 500)
        else:
            return make_response({"ERROR":"Failed to update user on mongodb"}, 500)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
    
def editUserToAzure(id, data):
    try:
        # print(data)
        tenant_id=os.environ.get("AZURE_TENANT_ID")
        # print(tenant_id)
        client_id=os.environ.get("AZURE_CLIENT_ID")
        # print(client_id)
        client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        # print(client_secret)
        # print('here')

        # client_id = "appId"
        # client_secret= "secret"
        # tenant_id = "tenantId"
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        # print('here')
        scopes = ['https://graph.microsoft.com/.default']
        # print('here')
        app = msal.ConfidentialClientApplication(client_id, client_secret, authority=authority)
        # print('here')
        result = app.acquire_token_for_client(scopes)
        # print('here')
        # print(result)
        access_token = result['access_token']
        # print(access_token)
        # print('here')
        headers = {'Authorization': 'Bearer ' + access_token}
        # print('here')

        user_object_id = id

        # Update URL for the specific user
        url = f"https://graph.microsoft.com/v1.0/users/{user_object_id}"

        update_parameters = {
            "displayName": f"{data['givenName']}",  
            "mailNickname": f"{data['givenName']}",
            "givenName":f"{data['FirstName']}",
            "userPrincipalName": f"{data['mail']}",
            "mail": f"{data['mail']}",
            "surname": f"{data['LastName']}",
            "usageLocation": f"{data['usageLocation']}"
        }

        response = requests.patch(url, headers=headers, json=update_parameters)

        if response.status_code == 204:
            # print('User details updated successfully!')
            return True
        else:
            # print(f"Failed to update user: {response.text}")
            return False
    except Exception as e:
        print("Error in Editing user on Azure: ",str(e))

def deleteUser(data):
    try:
        id = data['id']
        response = employeeData.delete_one({'id':UUID(id)})
        if response.deleted_count == 1:
            if deleteUserFromAzure(id):
                return make_response({"message":"User Deleted"}, 200)
            else:
                return make_response({"ERROR":"Failed to delete user from Azure"}, 500)
        else:
            return make_response({"ERROR":"Failed to delete user from mongodb"})
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)
    
def deleteUserFromAzure(id):
    try:
        # print(data)
        tenant_id=os.environ.get("AZURE_TENANT_ID")
        # print(tenant_id)
        client_id=os.environ.get("AZURE_CLIENT_ID")
        # print(client_id)
        client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        # print(client_secret)
        # print('here')

        # client_id = "appId"
        # client_secret= "secret"
        # tenant_id = "tenantId"
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        # print('here')
        scopes = ['https://graph.microsoft.com/.default']
        # print('here')
        app = msal.ConfidentialClientApplication(client_id, client_secret, authority=authority)
        # print('here')
        result = app.acquire_token_for_client(scopes)
        # print('here')
        # print(result)
        access_token = result['access_token']
        # print(access_token)
        # print('here')
        headers = {'Authorization': 'Bearer ' + access_token}
        # print('here')

        user_object_id = id

        # Update URL for the specific user
        url = f"https://graph.microsoft.com/v1.0/users/{user_object_id}"

        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            return True
        else:
            return False
    except Exception as e:
        print("Failed to delete user: ",str(e))