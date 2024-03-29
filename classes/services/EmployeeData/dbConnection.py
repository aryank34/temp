import base64
from typing import ByteString
from flask import make_response,jsonify, send_file,request
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from gridfs import GridFS
# from werkzeug.utils import secure_filename
#to get Object Id from mongodb
from bson.objectid import ObjectId

#load and find the env file
from dotenv import load_dotenv, find_dotenv
import os

#to compare UUID
from bson.binary import UuidRepresentation
from uuid import UUID

#to create expiry time of token (1 day)
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
# mongo_password = os.environ.get("MONGO_PWD")
mongo_host = os.environ.get("MONGO_HOST_prim")

#python-mongo connection string
uri = mongo_host
client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")

db = client.EmployeeDB

employeeData = client.EmployeeDB.employeeData

fs = GridFS(db)  
fs = GridFS(db, collection='employeeData')

def checkUserValidity(id):
    try:
        # print(UUID(uid))
        #get the user by matching the uuid from db
        # user = userProvisioningData.find_one({'id':UUID(uid)},{'_id':0,'Name':1,'id':1})
        user = employeeData.find_one({'id':UUID(id)},{'_id':0,'FirstName':1,'LastName':1,'id':1,"Role":1,"status":1})
        if user:
            #set total Active employees
            setTotalEmployees()
            if user['status'] == 'Active':
                user['id'] = str(user['id']) #uuid cant be sent directly, convert to string first
                # print(user)

                profile_picture = get_profile_picture(id)
                if profile_picture is None:
                    profile_picture=""

                #create a token

                #set expiry time of token
                exp_time = datetime.now() + timedelta(days=1) #1 day expiry time
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

                #set total active employees
                setTotalEmployees()

                return make_response({"token":jwtoken,"profile_picture":profile_picture}, 200)
            elif user['status'] == 'Non-Active':
                return make_response({"ERROR":"User is Not-Active"}, 500)
        else:
            return make_response({"ERROR":"No User Found"}, 404)

    except Exception as e:
        # print(e)
        return make_response({"message":str(e)}, 500)

#giving NA to replace empty value
def replace_null(value, placeholder='NA'):
    return placeholder if value is None else value

def get_profile_picture(id):
    try:
        file_data = employeeData.find_one({'id': UUID(id)}, {'_id': 0, 'profile_picture_id': 1})
        if file_data and 'profile_picture_id' in file_data:
            file_id = file_data['profile_picture_id']
            file_doc = fs.get(file_id)
            file_extension = file_doc.content_type.split("/")[1]
            encoded_image = base64.b64encode(file_doc.read()).decode('utf-8')
            return f"data:image/{file_extension};base64,{encoded_image}"
        else:
            return ""
    except Exception as e:
        return str(e)

#get data from mongodb
def get_employee_data(id):
    try:
        
        employee = list(employeeData.find({'id':UUID(id)},{'_id':0,'id':1,'emp_id':1,'FirstName':1,'LastName':1,'mail':1,'team':1,'Designation':1,'ContactNo':1,'Address':1,'ReportingTo':1,'status':1,'Date_of_Joining':1,'Emergency_Contact_Name':1,'Emergency_Contact_Number':1,'Emergency_Relation':1,'Certificate_Name':1, 'profile_picture_id':1, 'Last_modification':1}))[0]
        if "profile_picture_id" not in employee:
            employee["profile_picture_id"] = ""
        else:

            employee["profile_picture_id"]= str(employee["profile_picture_id"])
        # print(employee)
        profile_picture = get_profile_picture(id)
        # print(profile_picture)
        if profile_picture:
           
            employee['profile_picture'] = profile_picture
            # print (type(employee['profile_picture']))
            # print(employee)

        
        return make_response(jsonify(employee), 200)
        # return make_response({"message":employee}, 200)
   
    except Exception as e:
        return make_response({"Error is fetching basic info: ",e}, 500)

"""
emp = get_employee_data()
for emp in emp:
    printer.pprint(emp)
    print("\n")

"""

def setTotalEmployees():
    count = employeeData.count_documents({'status':'Active'})
    db.StaticData.update_one({},{"$set":{'totalActiveEmployees':count}})

#to update the data in the database
def edit_employee_data(data_obj, id):
    try:
        #send these object fields to database
        # print(data_obj)
        # print(id)
        data_obj['Last_modification'] = datetime.today().strftime('%Y-%m-%d')
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
        return make_response({"message":"No File Data"}, 200)
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

def Upload_profile_picture(id):
    try:
        
            profile_picture = request.files['profile_picture']
            # print(profile_picture)
            if profile_picture is not None:
                filename = secure_filename(profile_picture.filename)
                # print(f"Uploading profile picture: {filename}")
                  
            # Fetch the user from MongoDB based on the unique ID
                employeeData = db.employeeData.find_one({'id': UUID(id)})
                existing_user = db.employeeData.find_one({'id': UUID(id)})
                if existing_user:
                # Check if the user has an existing profile picture
                    if existing_user.get('profile_picture_id'):
                    # Delete the previous profile picture
                        previous_picture_id = existing_user['profile_picture_id']
                        fs.delete(previous_picture_id)
                        # print(f"Previous profile picture deleted for user {id}.")
    
        
            
                if employeeData:
                        # Save file to MongoDB using GridFS
                        grid_file= fs.put(profile_picture.stream, filename=filename, content_type=profile_picture.content_type, id=UUID(id)) 
        
                        # Associate the file with the user in the employeeData collection
                        db.employeeData.update_one({'id': UUID(id)}, {'$set': {'profile_picture_id':grid_file}})
                        print(f"Profile picture {filename} uploaded successfully.")
                        return jsonify({'success': 'Profile picture uploaded successfully'}), 200
                else:
                    return 'User not found', 404
            else:
                return 'File not provided', 400
    except Exception as e:
 
        return make_response({"ERROR":"File not available"}, 500)







