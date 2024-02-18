from flask import make_response,jsonify, send_file
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

#upload documents
from werkzeug.utils import secure_filename
from gridfs import GridFS

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
db = client.sample_employee
employeeData = client.sample_employee.employeeData
userProvisioningData = client.sample_employee.UserProvisioningData

def checkUserValidity(id):
    try:
        # print(UUID(uid))
        #get the user by matching the uuid from db
        # user = userProvisioningData.find_one({'id':UUID(uid)},{'_id':0,'Name':1,'id':1})
        user = employeeData.find_one({'id':UUID(id)},{'_id':0,'FirstName':1,'LastName':1,'id':1,"Role":1})

        user['id'] = str(user['id']) #uuid cant be sent directly, convert to string first
        # print(user)

        #create a token

        #set expiry time of token
        exp_time = datetime.now() + timedelta(hours=1) #1 hour expiry time
        exp_epoch_time = int(exp_time.timestamp())
        # print(exp_epoch_time)

        #payload
        payload = {
            "payload": user,
            "exp": exp_epoch_time
        }
        # print(payload)

        #secret key
        secret = os.environ.get('SECRET_KEY')
        algo = os.environ.get('ALGORITHM')
        # print(algo)

        #jwtoken
        jwtoken = jwt.encode(payload, secret, algorithm=algo)
        # print(jwt.encode(payload, secret, algorithm=algo))

        return make_response({"token":jwtoken}, 200)

    except Exception as e:
        # print(e)
        return make_response({"message":str(e)}, 500)

#giving NA to replace empty value
def replace_null(value, placeholder='NA'):
    return placeholder if value is None else value

#get data from mongodb
def get_employee_data(id):
    try:
        employees = employeeData.find({'id':UUID(id)},{'_id':0,'id':1,'emp_id':1,'FirstName':1,'LastName':1,'mail':1,'team':1,'Designation':1,'ContactNo':1,'Address':1,'ReportingTo':1,'status':1,'Date_of_Joining':1,'Emergency_Contact_Name':1,'Emergency_Contact_Number':1,'Emergency_Relation':1})
        all_employee_data = [
            {
                # '_id': str(ObjectId(emp['_id'])),
                'id': replace_null(str(emp.get('id'))),
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
                'Emergency_Contact_Name': replace_null(emp.get('Emergency_Contact_Name')),
                'Emergency_Contact_Number': replace_null(emp.get('Emergency_Contact_Number')),
                'Emergency_Relation': replace_null(emp.get('Emergency_Relation')),
                'emp_id': replace_null(emp.get('emp_id'))
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
def edit_employee_data(data_obj, id):
    try:
        #send these object fields to database
        # print(data_obj)
        # print(id)
        data_obj = {
            "$set":data_obj
        }
        #update the user data using this id and data_obj
        #employeeData.update_one({"id":logged_in_user_id}, data_obj) #use this for production app

        if(employeeData.count_documents({"id":UUID(id)},limit = 1) == 1):
            employeeData.update_one({"id":UUID(id)}, data_obj) 
            return make_response({"message":"Data Edited"}, 201)
        else:
            return make_response({"message":"No record Found"},202)
    except Exception as e:
        error_message = str(e)
        return ({'error in updatingMongoDb': error_message}, 500)

def check_documents(id):
    # try:
        # result = employeeData.find_one({"id":UUID(id)},{"_id":0,"file_id":1})
    emp = employeeData.find_one({"id":UUID(id)})
    # obj = {'aadhar':False,'pan':False}
    # obj={}
    if 'file_id' in emp:
    # print(result)
        result = emp['file_id']
        obj = {key: True for key in result.keys()}
        # if 'aadhar' in result:
        #     obj['aadhar'] = True
        # if 'pan' in result:
        #     obj['pan'] = True
        # print(obj)
        return make_response({"Message":obj}, 200)
    else:
        return make_response({"Message":obj}, 200)
    # except Exception as e:
    #     return make_response({"ERROR":str(e)})

def upload_documents(id, file_response):
    # fs = GridFS(db)  
    fs = GridFS(db, collection='employeeData')
    # print(list(file_response))
    # file_field = ""
    # # if list[file_response][0] == 'aadhar':
    # if 'aadhar' in file_response:
    #     file_field = 'aadhar'
    # # elif list[file_response][0] == 'pan':
    # elif 'pan' in file_response:
    #     file_field = 'pan'
    # print(file_field)
    file_field = list(file_response)[0]
    # print(file_field)
    file_data = file_response[file_field]
    # print(file_data)

    if file_data is not None:
        filename = secure_filename(file_data.filename)
                
        # Fetch the user from MongoDB based on the unique ID
        

        employeeData =  db.employeeData.find_one({'id': UUID(id)})
        # print(employeeData)
        if "file_id" in employeeData:
            file_id = employeeData['file_id']
            # print(file_id)
            if file_field in file_id:
                #aadhar or pan
                file_obj_id = file_id[file_field]
                # print(file_obj_id)
                #delete previous file to save new one
                fs.delete(file_obj_id)

        # try:
        #     file_data = employeeData.find_one({'id':UUID(id)},{'_id':0,f'file_id.{file_field}':1})
        #     print(file_data)
        # except:
        #     return make_response({"ERROR":f"No {file_field} document"}, 404)
        
        if employeeData:    
            # Save file to MongoDB using GridFS
            #with fs.new_file(filename=file_data, content_type=file_data.content_type) as grid_file:
            got_file= fs.put(file_data.stream, filename=filename, content_type=file_data.content_type, id=UUID(id))
            
            #object to save in every employees db
            # file_obj = {
            #     file_field:got_file,
            # }
            
            # Associate the file with the user in the employeeData collection
            db.employeeData.update_one({'id': UUID(id)}, {'$set': {f'file_id.{file_field}':got_file}})

            return make_response({"message":'Document Successfully Uploaded'}, 200)
        else:
            return make_response({"message":'User not found'}, 404)
    else:
        return make_response({"message":'File not provided'}, 400)
    

def send_document(id,file_type):
    try:
        fs = GridFS(db, collection='employeeData')
        try:
            file_data = employeeData.find_one({'id':UUID(id)},{'_id':0,f'file_id.{file_type}':1})
        # print(file_data)
        except:
            return make_response({"ERROR":f"No {file_type} document"}, 404)
        file_id = file_data['file_id'][file_type]
        # print(file_id)
        file_doc= fs.get(file_id)
        file_extension = file_doc.content_type.split("/")[1]
        filename = f"{file_type}.{file_extension}"
        # print(filename)

        # print(aadhar)
        return send_file(file_doc, mimetype=file_doc.content_type, download_name=f"{filename}")
    except Exception as e:
        return make_response({"ERROR":"File not available"}, 500)






