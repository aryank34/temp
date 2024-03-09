from flask import Blueprint, request, make_response, jsonify
from ..loginAuth.tokenAuth import tokenAuth
from classes.services.contractRenewal.dbConnection import add_account, add_product, addnew_cert, delete_account, delete_at_cert, delete_product, get_all_document, get_document_info, edit_subscription
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
            result = get_document_info(id)
            return result

    
    return result

@contract_renewal.route("/dashboard/contract/addaccount", methods=['POST'])
@auth.token_auth("/dashboard/contract/addaccount")
def addaccount():
    try:       
        
        if request.method == 'POST':
            result= add_account()
            
            return result
        else:
                
            return jsonify({'error'}), 400
            
    except Exception as e:
    # Handle any potential exceptions (e.g., invalid JSON format)
        return jsonify({'error': f'Error processing JSON payload: {str(e)}'}), 400
    

@contract_renewal.route("/dashboard/contract/addproduct", methods=['POST'])
@auth.token_auth("/dashboard/contract/addproduct")
def addproduct():
    try:       
        
        if request.method == 'POST':
            result= add_product()
            
            return result
        else:
                
            return jsonify({'error'}), 400
            
    except Exception as e:
    # Handle any potential exceptions (e.g., invalid JSON format)
        return jsonify({'error': f'Error processing JSON payload: {str(e)}'}), 400


# _id of the company account is compulsory
@contract_renewal.route("/dashboard/contract/deleteaccount", methods=['GET', 'DELETE'])
@auth.token_auth("/dashboard/contract/deleteaccount")
def deleteAcoount():
    try:
        if request.method == 'DELETE':
            result = delete_account()

        return make_response(jsonify("account deleted successfully"), 200)
    except Exception as e:
        return make_response({'error in contractrenewal': str(e)}), 500
    
# company_id of the company account
# and _id of the product is compulsory
@contract_renewal.route("/dashboard/contract/deleteproduct", methods=['GET', 'DELETE'])
@auth.token_auth("/dashboard/contract/deleteproduct")
def deleteProduct():
    try:
        if request.method == 'DELETE':    
            result = delete_product()

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
    

#in Delete Specific certificate json body must have object id and the index number of the cert to be deleted
@contract_renewal.route("/dashboard/contract/edit/delete", methods=['DELETE'])
@auth.token_auth("/dashboard/contract/edit/delete")
def delete_cert():
    try:
        if request.method == 'DELETE':
            # Call the edit_subscription function with _id
            result = delete_at_cert()
       
            # Return the subscription data as JSON using jsonify
            return result


    except Exception as e:
        return make_response(jsonify({'error in contractrenewal': str(e)}), 500)
    

#in add new certificate json body must have 
#object id, certificate name and expiry of the certificate to add
@contract_renewal.route("/dashboard/contract/edit/add", methods=['POST'])
@auth.token_auth("/dashboard/contract/edit/add")
def add_cert():
    try:
        if request.method == 'POST':
            # Call the edit_subscription function with _id
            result = addnew_cert()
       
            # Return the subscription data as JSON using jsonify
            return result


    except Exception as e:
        return make_response(jsonify({'error in contractrenewal': str(e)}), 500)