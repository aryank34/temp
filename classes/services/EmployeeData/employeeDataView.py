from .dbConnection import Upload_profile_picture, get_employee_data,edit_employee_data,upload_documents, send_document, check_documents
from flask import jsonify, Blueprint, request, make_response
from ..loginAuth.tokenAuth import tokenAuth


#create object of authMongo class
auth = tokenAuth()

#it tells that this file has a bunch of URLs defined in it
employeeDataView = Blueprint('employeeDataView',__name__)

@employeeDataView.route("/dashboard/employeedata",methods = ['GET'])
@auth.token_auth("/dashboard/employeedata")
#get data from database and send it to frontend
def send_employee_data():
    try:
        if request.method == 'GET':
            id = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
            # print(id)

            #get employee data basic info and send it to frontend
            # result= make_response({"message": get_employee_data(id)},200)
            # return result
            return get_employee_data(id)
        # if request.method == 'GET':
        #     return make_response('',204)
    
    except Exception as e:
        error_message = str(e)
        return make_response(jsonify({'error in displayingEmployeeData': error_message}), 500)
    
#send_employee_data()
#now register this blueprint in __init__.py file


#get data from frontend, validate the data, mask the data and then update in the database
@employeeDataView.route("/dashboard/employeedata/edit", methods = ['GET', 'PUT'])
@auth.token_auth("/dashboard/employeedata/edit")
def editEmployeeData():
    try:
        if request.method == 'PUT':
            # uid = request.json.get('id') #not used currently, will be used in SuperAdmin properties to CRUD
            id = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
            FirstName = request.json.get('FirstName')
            LastName = request.json.get('LastName')
            ContactNo = request.json.get('ContactNo')
            Address = request.json.get('Address')
            Emergency_Contact_Name = request.json.get('Emergency_Contact_Name')
            Emergency_Contact_Number = request.json.get('Emergency_Contact_Number')
            Emergency_Relation = request.json.get('Emergency_Relation')
            Date_of_Joining = request.json.get("Date_of_Joining")

            #use after frontend sends the correct token with this data - i think
            # payload = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']
            
        
            # id = payload['id']
            # FirstName = payload['FirstName']
            # LastName = payload['LastName']
            # ContactNo = payload['ContactNo']
            # Address = payload['Address']
            # Emergency_Contact_Name = payload['Emergency_Contact_Name']
            # Emergency_Contact_Number = payload['Emergency_Contact_Number']
            # Emergency_Relation = payload['Emergency_Relation']

            #printer.pprint(name)
            emp_obj = {"FirstName":FirstName,
                    "LastName":LastName,
                    "ContactNo":ContactNo,
                    "Address":Address,
                    "Date_of_Joining":Date_of_Joining,
                    "Emergency_Contact_Name":Emergency_Contact_Name,
                    "Emergency_Contact_Number":Emergency_Contact_Number,
                    "Emergency_Relation":Emergency_Relation}
            #update the data in the database
            
            return edit_employee_data(emp_obj, id)
            

        #return "Edit Page"
        # return render_template("getData.html")
        if request.method == 'GET':
            return make_response('',201)
    except Exception as e:
        # print("error")
        error_message = str(e)
        return make_response(jsonify({'error in editEmployeeData': error_message}), 500)
    

#get the documents/files from frontend, save it in a location, then save the path in mongodb
@employeeDataView.route('/dashboard/employeedata/documents', methods=['GET','POST'])
@auth.token_auth("/dashboard/employeedata/documents")
def getEmployeeDocuments():
    '''
    1. uploading file to server
    2. saving file to filesystem with unique filename
    3. uploading filepath in database with respective employee
    4. creating an endpoint to read the file
    '''
    id = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
    if request.method == 'POST':
        # Extract file in form of json JSON 
        #uid = request.json.get('id') #not used currently, will be used in SuperAdmin properties to CRUD
        # print(id)
        # file_data = request.files['file']
        return upload_documents(id, request.files)

        # return upload_documents(id, file_data)
    if request.method == 'GET':
        return check_documents(id)

# @employeeDataView.route("/dashboard/employeedata/documents/aadhar", methods=['GET'])
@employeeDataView.route("/dashboard/employeedata/documents/<any>", methods=['GET'])
@auth.token_auth("/dashboard/employeedata/documents/<any>")
# @auth.token_auth("/dashboard/employeedata/documents/aadhar")
# @auth.token_auth("/dashboard/employeedata/documents/pan")

def downloadDocument(any):
    try:
        # print(any)
        id = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
        return send_document(id,any)
        # return send_document(id,'aadhar')
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)


    
# @employeeDataView.route("/dashboard/employeedata/documents/pan", methods=['GET'])
# @auth.token_auth("/dashboard/employeedata/documents/pan")
# def downloadPan():
#     try:
#         id = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
#         return send_document(id,'pan')
#     except Exception as e:
#         return make_response({"ERROR":str(e)}, 500)
    
@employeeDataView.route('/dashboard/employeedata/uploadprofilepicture', methods=['POST'])
@auth.token_auth("/dashboard/employeedata/uploadprofilepicture")

def upload_profile_pic():
    id = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
    result= Upload_profile_picture(id)

    return result