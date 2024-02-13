from flask import make_response,jsonify
from pymongo import MongoClient

#to get Object Id from mongodb
from bson.objectid import ObjectId

#load and find the env file
from dotenv import load_dotenv, find_dotenv
import os

#to compare UUID
from bson.binary import UuidRepresentation
from uuid import UUID

#to create expiry time of token (15mins)
from datetime import datetime, timedelta

load_dotenv(find_dotenv())

#for creating jwt 
# import jwt
import jwt


# import sys
# print(sys.path)

#database connection
#get the fields from .env file
mongo_password = os.environ.get("MONGO_PWD")

#python-mongo connection string
connection_string = f"mongodb+srv://admin:{mongo_password}@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string, UuidRepresentation="standard")
employeeData = client.sample_employee.employeeData
userProvisioningData = client.sample_employee.UserProvisioningData

def checkUserValidity(uid):
    try:
        # print(UUID(uid))
        #get the user by matching the uuid from db
        user = userProvisioningData.find_one({'id':UUID(uid)},{'_id':0,'Name':1,'id':1})
        user['id'] = str(user['id']) #uuid cant be sent directly, convert to string first
        # print(type(user))

        #create a token

        #set expiry time of token
        exp_time = datetime.now() + timedelta(minutes=15) #15 minutes expiry time
        exp_epoch_time = int(exp_time.timestamp())

        #payload
        payload = {
            "payload": user,
            "exp": exp_epoch_time
        }
        print(payload)

        #secret key
        secret = os.environ.get('SECRET_KEY')

        #jwtoken
        jwtoken = jwt.encode(payload, secret, algorithm="HS256")
        print(jwtoken)

        return make_response({"token":jwtoken}, 200)

    except Exception as e:
        print(e)
        return make_response({"message":"No User Found"}, 500)

#giving NA to replace empty value
def replace_null(value, placeholder='NA'):
    return placeholder if value is None else value

#get data from mongodb
def get_employee_data(id):
    try:
        employees = employeeData.find({'emp_id':id},{'id':1,'FirstName':1,'LastName':1,'mail':1,'team':1,'Designation':1,'ContactNo':1,'Address':1,'ReportingTo':1,'status':1,'Date_of_Joining':1,'Designation':1})
        
        all_employee_data = [
            {
                '_id': str(ObjectId(emp['_id'])),
                'id': replace_null(str(emp.get('id').hex())),
                'FirstName': replace_null(emp.get('FirstName')),
                'LastName': replace_null(emp.get('LastName')),
                'mail': replace_null(emp.get('mail')),
                'team': replace_null(emp.get('team')),
                'Designation': replace_null(emp.get('Designation')),
                'ContactNo': replace_null(emp.get('ContactNo')),
                'Address': replace_null(emp.get('Address')),
                'ReportingTo': replace_null(emp.get('ReportingTo')),
                'status': replace_null(emp.get('status')),
                'Date_of_Joining': replace_null(emp.get('Date_of_Joining')),
                'status': replace_null(emp.get('status')),
                'Date_of_Joining': replace_null(emp.get('Date_of_Joining')),
            }
            for emp in employees

        ]
        #send data to frontend
        return make_response(jsonify(all_employee_data[0]), 201)
    
    except Exception as e:
        return make_response({"Error is fetching basic info: ",e}, 500)

"""
emp = get_employee_data()
for emp in emp:
    printer.pprint(emp)
    print("\n")

"""

#to update the data in the database
def edit_employee_data(data_obj, uid=1):
    try:
        #send these object fields to database
        # print(data_obj)
        data_obj = {
            "$set":data_obj
        }
        #update the user data using this id and data_obj
        #employeeData.update_one({"id":logged_in_user_id}, data_obj) #use this for production app

        if(employeeData.count_documents({"emp_id":uid},limit = 1) == 1):
            employeeData.update_one({"emp_id":uid}, data_obj) #only for development check
            return make_response({"message":"Data Edited"}, 201)
        else:
            print("here")
            return make_response({"message":"No record Found"},202)
    except Exception as e:
        error_message = str(e)
        return ({'error in updatingMongoDb': error_message}, 500)





