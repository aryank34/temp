from flask import Flask, make_response
from flask import jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta
import os
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient
from bson import ObjectId
from pymongo.server_api import ServerApi

# from classes.services.contractRenewal.RenewalMail import send_reminder

load_dotenv(find_dotenv())
mongo_host = os.environ.get("MONGO_HOST_prim")
uri = mongo_host
client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")
# client = MongoClient(connection_string)
contract_renewal = client.contract_renewal
subscription = contract_renewal["subscription"]
subscriptionDB = contract_renewal["subscriptionDB"]
products_services = contract_renewal['products_services']


# 
# edit how the date is recieved and send to the database as it is not in date object
# 
def parse_date(date_string):
    if date_string:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    return None

def get_all_document():
    
    try:
        # Query the database to get the required information
        cursor = subscriptionDB.find({})
        
        # Extract information from the cursor
        result = []
        for document in cursor:
            _id = str(document["_id"])
            company_name = document["company_name"]

            products_data = []

            for product_info in document["product"]:
                product_id = str(product_info["product_id"])
                product_name = product_info["product_name"]

                product_data = {
                    "product_id": product_id,
                    "product_name": product_name,
                }
                products_data.append(product_data)

            data = {
                "_id": _id,
                "company_name": company_name,
                "products": products_data
            }
            result.append(data)

        # Return the result as a JSON file
        return jsonify(result)

    except Exception as e:
        # Handle exceptions and return an error message
        error_message = {"error": str(e)}
        return jsonify(error_message), 500
    
    
documents = list(contract_renewal.products_services.find({}))
def get_document_info(_id):
    try:
        if _id is None:
            return jsonify({"error": "Missing _id parameter"}), 400

        document = contract_renewal.products_services.find_one({'_id': ObjectId(_id)})
        if document:
            # Fetch additional information from subscription collection using company_id
            company_id = document.get('company_id')
            subscription_document = contract_renewal.subscriptionDB.find_one({'_id': ObjectId(company_id)})
           
        

            if document:
                # Format the data for sending to the frontend
                formatted_data = {
                    "_id": str(document.get("_id", "")),
                    "product_name": document.get("product_name",""),
                    "company_id": str(document.get("company_id", "")),
                    "company_name": document.get("company_name", ""),
                    "company_address": subscription_document.get("company_address", ""),
                    "status": subscription_document.get("status", ""),
                    "point_of_contact": subscription_document.get("point_of_contact", []),
                    "quantity": document.get("quantity", ""),
                    "price": document.get("price", ""),
                    "start_date": document.get("start_date", ""),
                    "end_date": document.get("end_date", ""),
                    "duration": document.get("duration"),
                     "certificates_details": [
                    {
                        "index": i,
                        "certificate_name": cert.get("certificate_name", ""),
                        "expiry_date": cert.get("expiry_date", "")
                    } for i, cert in enumerate(document.get("certificates_details", []))
                ],
                }
                # Convert the cursor to a list and handle the result
                # The result is a list, but since we are matching on _id, there should be only one document
                return make_response({"message": formatted_data }, 200)
            else:
                    return make_response({"error": "Subscription document not found"}, 404)
        else:
            return make_response({"error": "Product document not found"}, 404)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# def add_account():
#     try:
#         data = request.json
#         company_name = data.get("company_name", "")
#         formatted_account = {
#             "company_name": company_name,

#             # Add more fields as needed
#         }
#         result = subscriptionDB.insert_one(formatted_account)
#         return jsonify({"message": "Account added successfully", "company_id": str(result.inserted_id), "company_name": company_name})
#     except Exception as e:
#         return jsonify({"error": str(e)})
    
def add_account():
    try:
        data = request.json

        # Set default values if not provided
        product_data = data.get("product", [])
        company_address = data.get("company_address", None)

        # Format account data
        formatted_data = {
            "company_name": data.get("company_name", ""),
            "product": product_data,
            "company_address": company_address,
            "status": data.get("status", ""),
            "point_of_contact": data.get("point_of_contact", [])
        }

        result = contract_renewal.subscriptionDB.insert_one(formatted_data)
        return jsonify({"message": "Account added successfully", "account_id": str(result.inserted_id)})
    except Exception as e:
        return jsonify({"error": str(e)})

def add_product():
    try:
        data = request.json
        company_id = data.get("company_id")
        account_data = subscriptionDB.find_one({"_id": ObjectId(company_id)})
        certificates_details= data.get("certificates_details", [])
        if account_data:
            formatted_product = {
                "product_name": data.get("product_name", ""),
                "company_id": company_id,
                "company_name": data.get("company_name", ""),
                "certificates_details": certificates_details,
                "point_of_contact": data.get("point_of_contact", []),
                "duration": data.get("duration", ""),
                "start_date": data.get("start_date", ""),
                "end_date": data.get("end_date", ""),
                "price": data.get("price", ""),
                "quantity": data.get("quantity", ""),
                # Add more fields as needed
            }
            result = products_services.insert_one(formatted_product)

            # Update the company_id reference in products_services
            products_services.update_one(
                {"_id": ObjectId(result.inserted_id)},
                {"$set": {"company_id": ObjectId(company_id)}}
            )

            # Update the product_id and company_id references in subscriptionDB
            subscriptionDB.update_one(
                {"_id": ObjectId(company_id)},
                {
                    "$push": {"product": {"product_id": result.inserted_id, "product_name": formatted_product["product_name"]}}
                }
            )

            return jsonify({"message": "Product added successfully", "product_id": str(result.inserted_id)})
        else:
            return jsonify({"error": "Account not found"})
    except Exception as e:
        return jsonify({"error": str(e)})


def delete_account():
    
    try:
        data = request.json
        _id = data.get("_id")
        account_data = subscriptionDB.find_one({"_id": ObjectId(_id)})

        if account_data:
            # Extract product IDs from the account_data
            products_data = []

            for product_info in account_data["product"]:
                product_id = str(product_info["product_id"])
                products_data.append(product_id)

            # Delete products in products_services collection
            result = contract_renewal.products_services.delete_many({"_id": {"$in": [ObjectId(pid) for pid in products_data]}})

            # Delete the account in subscriptionDB
            contract_renewal.subscriptionDB.delete_one({"_id": ObjectId(_id)})

            return jsonify({"message": "Account and associated products deleted successfully", "deleted_products_count": result.deleted_count})
        else:
            return jsonify({"error": "Account not found"})
    except Exception as e:
        return jsonify({"error": str(e)})

def delete_product():
    try:
        data = request.json
        product_id = data.get("_id")
        company_id = data.get("company_id")

        # Delete product from products_services collection
        result = contract_renewal.products_services.delete_one({"_id": ObjectId(product_id)})

        if result.deleted_count > 0:
            # Remove product entry from product array in subscriptionDB
            subscriptionDB.update_one(
                {"_id": ObjectId(company_id)},
                {"$pull": {"product": {"product_id": ObjectId(product_id)}}}
            )

            return jsonify({"message": "Product deleted successfully"})
        else:
            return jsonify({"error": "Product not found"})
    except Exception as e:
        return jsonify({"error": str(e)})


def edit_subscription(id,json_data):
    try:

        # Extract the _id from the JSON data
        _id = json_data.get('_id')
        document = contract_renewal.subscription.find_one({"_id": ObjectId(id)})
        document['_id'] = str(document['_id'])
        get_document_info(id)
        if not _id:
                return make_response({"error": "Account ID is required"},400)
        #data from frontend 
        data = {
                'account_name': json_data.get('account_name'),
                'certificate_details': json_data.get('certificate_details'),
                'point_of_contact': json_data.get('point_of_contact')  # Assuming certificates is a list
            }
        
        # Check if the subscription with the given _id exists
        if (contract_renewal.subscription.count_documents({"_id": ObjectId(id) },limit= 1)==1):
            update_data = {
                    'account_name': data['account_name'],
                    'certificate_details': [
                        {
                            'certificate_name': cert.get('certificate_name'),
                            'expiry_date': cert.get('expiry_date')
                        } for cert in data['certificate_details']
                    ],
                    'point_of_contact': data['point_of_contact']
                }

             # Update the subscription details in the database
            result = contract_renewal.subscription.update_one(
                {'_id': ObjectId(id)},
                {'$set': update_data}
            )
        

            # return make_response({"message": result},200)

            # Check if the update was successful
        if result.modified_count > 0:
            return make_response({"message": "Subscription updated successfully"},201)
        else:
            return make_response({"message": "no record found"},202)
        
    except Exception as e:
        return make_response(({'error in dbconnect2': str(e)}), 500)
    

def delete_at_cert():
    try:
        _id = request.json.get("_id")
        certificate_index = request.json.get("index")
        
        # Use ObjectId to convert the string to BSON ObjectId
        result = contract_renewal.subscription.update_one(
            {"_id": ObjectId(_id)},
            {
                "$set": {
                    f"certificate_details.{certificate_index}": None
                }
            }
        )

        if result.modified_count > 0:
            contract_renewal.subscription.update_one(
                {"_id": ObjectId(_id)},
                {"$pull": {"certificate_details": None}}
            )
            return jsonify({"message": "Certificate deleted successfully"})
        else:
            return jsonify({"message": "Certificate not found"})
    except Exception as e:
        return jsonify({"error": str(e)})
    

def addnew_cert():
    try:
        _id = request.json.get("_id")
        certificate_name = request.json.get("certificate_name")
        expiry_date = request.json.get("expiry_date")
        
        # Use ObjectId to convert the string to BSON ObjectId
        result = contract_renewal.subscription.update_one(
            {"_id": ObjectId(_id)},
            {"$push": {"certificate_details": {"certificate_name": certificate_name, "expiry_date": expiry_date}}}
        )

        if result.modified_count > 0:
            return jsonify({"message": "Certificate added successfully"})
        else:
            return jsonify({"message": "Failed to add certificate"})
    except Exception as e:
        return jsonify({"error": str(e)})