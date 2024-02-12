from flask import make_response,jsonify
from pymongo import MongoClient

#to get Object Id from mongodb
from bson.objectid import ObjectId

#load and find the env file
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

#Pretty printer - dev mode only
import pprint
printer = pprint.PrettyPrinter()

#database connection
#get the fields from .env file
mongo_password = os.environ.get("MONGO_PWD")

#python-mongo connection string
connection_string = f"mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)
employeeData = client.sample_employee.employeeData
userProvisioningData = client.sample_employee.UserProvisioningData

def checkUserValidity(uid):
    connection_string = f"mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    userProvisioningData = client.sample_employee.UserProvisioningData
    query = userProvisioningData.count_documents({'id': uid}, limit=1)
    
    return  make_response({"message": query != 0}, 200)

#giving NA to replace empty value
def replace_null(value, placeholder='NA'):
    return placeholder if value is None else value

#get data from mongodb
def get_employee_data(id):
    try:
        connection_string = f"mongodb+srv://admin:{mongo_password}@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(connection_string)
        employeeData = client.sample_employee.employeeData
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
        connection_string = f"mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(connection_string)
        employeeData = client.sample_employee.employeeData
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





