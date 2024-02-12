from .dbConnection import get_employee_data,edit_employee_data
from flask import jsonify, Blueprint, request, make_response

#Pretty printer - dev mode only
import pprint
printer = pprint.PrettyPrinter()

#it tells that this file has a bunch of URLs defined in it
employeeDataView = Blueprint('employeeDataView',__name__)

@employeeDataView.route("/employeeData",methods = ['GET', 'POST'])
#get data from database and send it to frontend
def send_employee_data():
    try:
        if request.method == 'POST':
            id = request.json.get('uid')
            
            #printer.pprint(list(emp))

            #get employee data basic info and send it to frontend
            return get_employee_data(id)
        if request.method == 'GET':
            return make_response('',204)
    
    except Exception as e:
        error_message = str(e)
        return make_response(jsonify({'error in displayingEmployeeData': error_message}), 500)
    
#send_employee_data()
#now register this blueprint in __init__.py file


#get data from frontend, validate the data, mask the data and then update in the database
@employeeDataView.route("/employeeData/edit", methods = ['GET', 'PATCH'])
def editEmployeeData():
    try:
        if request.method == 'PATCH':
            uid = request.json.get('uid')
            FirstName = request.json.get('FirstName')
            LastName = request.json.get('LastName')
            ContactNo = request.json.get('ContactNo')
            Address = request.json.get('Address')
            Emergency_Contact_Name = request.json.get('Emergency_Contact_Name')
            Emergency_Contact_Number = request.json.get('Emergency_Contact_Number')
            Emergency_Relation = request.json.get('Emergency_Relation')

            #printer.pprint(name)
            emp_obj = {"FirstName":FirstName,
                    "LastName":LastName,
                    "ContactNo":ContactNo,
                    "Address":Address,
                    "Emergency_Contact_Name":Emergency_Contact_Name,
                    "Emergency_Contact_Number":Emergency_Contact_Number,
                    "Emergency_Relation":Emergency_Relation}
            #update the data in the database
            
            return edit_employee_data(emp_obj, uid)
            

        #return "Edit Page"
        # return render_template("getData.html")
        if request.method == 'GET':
            return make_response('',201)
    except Exception as e:
        # print("error")
        error_message = str(e)
        return make_response(jsonify({'error in editEmployeeData': error_message}), 500)
    

#get the documents/files from frontend, save it in a location, then save the path in mongodb
@employeeDataView.route('/employeeData/documents', methods=['GET','POST'])
def getEmployeeDocuments(uid):
    '''
    1. uploading file to server
    2. saving file to filesystem with unique filename
    3. uploading filepath in database with respective employee
    4. creating an endpoint to read the file
    '''
    if request.method == 'POST':
        file = request.files['file']
        # file.save(f"/uploads/{file.filename}")
        return "File"
    if request.method == 'GET':
        return "Check File Path in db"
