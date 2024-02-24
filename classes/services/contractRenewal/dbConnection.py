import array
from flask import make_response
from flask import jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv, find_dotenv
# from flask_mail import Mail, Message  #pip3 install Flask-Mail
# from apscheduler.schedulers.background import BackgroundScheduler  #pip install apscheduler
from datetime import datetime, timedelta
import os


load_dotenv(find_dotenv())
mongo_password = os.environ.get("MONGO_PWD")
connection_string = f"mongodb+srv://admin:EC2024@employeeportal.yyyw48g.mongodb.net/"
client = MongoClient(connection_string)
contract_renewal = client.contract_renewal
collection = contract_renewal["subscription"]


def get_all_document():
    # Specify the projection to include only 'account_id' and 'account_name'
    projection = {'account_id': 1, 'account_name': 1, '_id': 1}

    # Use find with projection
    documents = list(contract_renewal.subscription.find({}, projection))
    
    # Create a list to store dictionaries for each document
    result = []
    
    for doc in documents:
        # Convert _id field to string
        doc['_id'] = str(doc['_id'])
        
        # Extract account_id and account_name
        account_id = doc.get('account_id', '')
        account_name = doc.get('account_name', '')
        
        # Create a dictionary with the required information
        doc_info = {
            "_id": doc['_id'],
            "account_id": account_id,
            "account_name": account_name
            # Add more fields as needed
        }
        
        # Append the dictionary to the result list
        result.append(doc_info)
    
    if result:
        # Return the list of dictionaries
        return make_response({"message": result}, 200)
    else:
        return jsonify({"error": "No documents found"}), 404



    
documents = list(contract_renewal.subscription.find({}))
def get_document_info(_id):
    try:
        if _id is None:
            return jsonify({"error": "Missing _id parameter"}), 400
        print(_id)

        document = contract_renewal.subscription.find_one({'_id': ObjectId(_id)})

        if document:
            # Format the data for sending to the frontend
            print(document)
            formatted_data = {
                "_id": str(document.get("_id", "")),
                "account_id": document.get("account_id", ""),
                "account_name": document.get("account_name", ""),
                "certificate_details": [
                    {
                        "certificate_name": cert.get("certificate_name", ""),
                        "expiry_date": cert.get("expiry_date", "")
                    } for cert in document.get("certificate_details", [])
                ],
                "point_of_contact": document.get("point_of_contact", "")
            }
            # Convert the cursor to a list and handle the result
                # The result is a list, but since we are matching on _id, there should be only one document
            return make_response({"message": formatted_data }, 200)
        else:
            return make_response({"error": "Document not found"}, 404)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    

def add_contractdetails():
    try:
        
            #fetch the data from frontend tht needs to be added
            data = {
                'account_id': request.json.get('account_id'),
                'account_name': request.json.get('account_name'),
                'certificate_details': request.json.get('certificate_details'),  # Assuming certificates is a list
                'point_of_contact': request.json.get('point_of_contact')
                #'start_date': request.json.get('start_date')

            }
            # Check if all required fields are present
            if all(data.values()):
            #if data is not None:
            #create a format of the document to be stored in mongoDB
                subscription_new = {
                    'account_id': data['account_id'],
                    'account_name': data['account_name'],
                    'certificate_details': [
                        {
                            'certificate_name': cert.get('certificate_name'),
                            'expiry_date': cert.get('expiry_date')
                        } for cert in data['certificate_details']
                    ],
                    'point_of_contact': data['point_of_contact']
                }
                #Insert into Mongo db
                contract_renewal.subscription.insert_one(subscription_new)
                return make_response({"message":"new subscription is added"}, 200) 
            else:
                return make_response({"ERROR":"Data is invalid"}, 500)
    except Exception as e:
        return make_response({"ERROR":str(e)}, 500)




    

            
def delete_subscription(_id):
    try:
        # Get subscription_id from the query parameters
            print (_id)

            if not _id:
                return jsonify({'message': 'account ID is required'}), 400
            
            document = contract_renewal.subscription.find_one({"_id": ObjectId(_id)})
            print(document)
            if not document:
                    return make_response({"error": "Document not found"}), 404
             
                    # Delete the record
            result = contract_renewal.subscription.delete_one({'_id': ObjectId(_id)})
            # response= make_response({"message: document deleted successfully": result}),200
            # return jsonify(response)                                        
            # Check if the deletion was successful
            if result.deleted_count > 0:
                return make_response({'message': 'Subscription deleted successfully'}), 200
            else:
                return make_response({'message': 'Error deleting subscription'}), 500
        

    except Exception as e:
        return make_response(jsonify({'error in dbconnect2': str(e)}), 500)



def edit_subscription(id,json_data):
    try:

        # Extract the _id from the JSON data
        _id = json_data.get('_id')
        document = contract_renewal.subscription.find_one({"_id": ObjectId(id)})
        document['_id'] = str(document['_id'])
        print(document)
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

            print(update_data)   
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
    

# # Flask-Mail configuration
# contract_renewal.config['MAIL_SERVER'] = 'smtp.office365.com'
# contract_renewal.config['MAIL_PORT'] = 587
# contract_renewal.config['MAIL_USE_TLS'] = True
# contract_renewal.config['MAIL_USE_SSL'] = False
# contract_renewal.config['MAIL_USERNAME'] = 'your_username'  #username of sender
# contract_renewal.config['MAIL_PASSWORD'] = 'your_password'  #password of sender
# contract_renewal.config['MAIL_DEFAULT_SENDER'] = 'your_email@example.com'   #mail id of sender

# mail = Mail(contract_renewal)

# # Background scheduler configuration
# scheduler = BackgroundScheduler()
# scheduler.start()


# def drafting_email(email, subscription_expiry_date):
#     with contract_renewal.app_context():
#         Msg = Message('Subscription Expiry Reminder', recipients=[email])
#         Msg. body = f"Your subscription will expire on {subscription_expiry_date}. Please renew it in time."
#         message= Mail.send(msg)
#         return message


# def send_reminder(id):
#     try:

#         # Get the current date
#         current_date = datetime.now()
#         _id = request.json.get( ObjectId(id))

#            # Fetch recipient email from MongoDB based on the Object ID
#         recipient = contract_renewal.subscription.find_one({'_id': _id})
#         if recipient:
#             recipient_email = recipient['email']
#             for sub in contract_renewal.subscription:
#                 expiry_date = contract_renewal.subscription['expiry_date']
              
#                 # Calculate the difference in days between the current date and the expiry date
#             days_until_expiry = (expiry_date - current_date).days

#             # Check if the expiry is within the next 60 days
#             if 0 <= days_until_expiry <= 60:
#                 # Schedule the reminder email 60 days before the expiry date
#                 # Schedule the reminder email 60 days before the expiry date
#                 scheduler.add_job(
#                     drafting_email,
#                     'date',
#                     run_date=expiry_date - timedelta(days=60),
#                     args=[contract_renewal.subscription['email'], expiry_date.strftime('%Y-%m-%d %H:%M:%S')]
#                 )
#         return make_response({'Reminder jobs scheduled successfully!'}, 500)
#     except Exception as e:
#         return make_response(({'error': str(e)}), 500)
            




    


