from operator import indexOf
from flask import Flask, Blueprint, request, make_response, jsonify, Response
from ..loginAuth.tokenAuth import tokenAuth
from classes.services.contractRenewal.dbConnection import add_contractdetails, get_all_document, get_document_info, edit_subscription,delete_subscription
from bson.objectid import ObjectId
auth = tokenAuth()

contract_renewal = Blueprint('contract_renewal', __name__)


#first route made to get all the data from database
@contract_renewal.route("/dashboard/contract/all", methods=['GET'])
@auth.token_auth("/dashboard/contract/all")
def get_allData():
    result= get_all_document()
    return result



# this route will display the information of one selected record
@contract_renewal.route('/dashboard/contract/<id>', methods=['GET'])
@auth.token_auth("/dashboard/contract/<id>")
def get_document(id):
    if request.method == 'GET':
            # _id=request.json["_id"]
            # _id = request.json.get("_id")
            # _id = str(_id)
            result = get_document_info(id)
            return result

    
    return result

@contract_renewal.route("/dashboard/contract/add", methods=['POST'])
@auth.token_auth("/dashboard/contract/add")
def add_contract_details():
    try:       
        
        if request.method == 'POST':
            id = tokenAuth.token_decode(request.headers.get('Authorization'))['payload']['id']
            
            result= add_contractdetails()
            
            return result
        else:
                
            return jsonify({'error'}), 400
            
    except Exception as e:
    # Handle any potential exceptions (e.g., invalid JSON format)
        return jsonify({'error': f'Error processing JSON payload: {str(e)}'}), 400

# _id is compulsory
@contract_renewal.route("/dashboard/contract/delete", methods=['GET', 'DELETE'])
@auth.token_auth("/dashboard/contract/delete")
def deleteContractRenewal():
    try:
        if request.method == 'DELETE':
        # Get JSON data from the request body
            json_data = request.json

            # Extract the _id from the JSON data
            _id = request.json["_id"]
            _id = request.json.get("_id")
            _id = str(_id)
            
            
            result = delete_subscription(_id)

           
        # return make_response(jsonify( result)), 200
        return make_response(jsonify("account deleted successfully"), 200)
    except Exception as e:
        return make_response({'error in contractrenewal': str(e)}), 500
    
#in edit json body must have _id
#account name, certificate details, point of contact all are compulsory fields
@contract_renewal.route("/dashboard/contract/edit", methods=['GET', 'PUT'])
@auth.token_auth("/dashboard/contract/edit")
def edit_subscription_data():
    try:
        if request.method == 'PUT':
            # Get JSON data from the request body
            json_data = request.json

            # Extract the _id from the JSON data
            _id = request.json["_id"]
            _id = request.json.get("_id")
            _id = str(_id)
            updated= json_data.get('new_data')

            # Call the edit_subscription function with _id
            response = edit_subscription(_id,json_data)
       
            # Return the subscription data as JSON using jsonify
            return response


    except Exception as e:
        return make_response(jsonify({'error in contractrenewal': str(e)}), 500)
