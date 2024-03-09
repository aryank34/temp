# from flask import make_response
# from flask import jsonify, request
# from pymongo import MongoClient
# from bson.objectid import ObjectId
# from dotenv import load_dotenv, find_dotenv
# from flask_mail import Mail, Message  #pip3 install Flask-Mail
# from apscheduler.schedulers.background import BackgroundScheduler  #pip install apscheduler
# from datetime import datetime, timedelta
# import os


# load_dotenv(find_dotenv())
# client = MongoClient(connection_string)
# contract_renewal = client.contract_renewal
# collection = contract_renewal["subscription"]

# def send_reminder():
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

from flask import Flask, render_template
from flask_socketio import SocketIO
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv
import os
from pymongo.server_api import ServerApi

app = Flask(__name__)
socketio = SocketIO(app)


# MongoDB setup
load_dotenv(find_dotenv())

mongo_host = os.environ.get("MONGO_HOST_prim")

#python-mongo connection string
uri = mongo_host
client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")
contract_renewal = client.contract_renewal
collection = contract_renewal["subscription"]

# Function to check and send notifications for upcoming expirations
def check_subscription_expirations():
    current_date = datetime.utcnow()
    sixty_days_from_now = current_date + timedelta(days=60)

    # Find subscriptions that expire within the next 60 days
    upcoming_expirations = collection.find({
        "certificate_details.expiry_date": {
            "$gte": current_date,
            "$lte": sixty_days_from_now
        }
    })

    for subscription in upcoming_expirations:
        # Extract relevant information (customize as needed)
        account_id = subscription.get("account_id")
        expiry_date = subscription.get("certificate_details")[0].get("expiry_date")

        # Send a notification to the frontend using WebSocket
        socketio.emit("expiration_notification", {
            "account_id": account_id,
            "expiry_date": expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        }, namespace="/notifications")

# Route to render a simple HTML page (optional)
# @app.route("/")
# def index():
#     return render_template("index.html")

# Configure the socketio to run in the "/notifications" namespace
@socketio.on("connect", namespace="/notifications")
def handle_connect():
    print("Client connected")

@socketio.on("disconnect", namespace="/notifications")
def handle_disconnect():
    print("Client disconnected")

# Schedule the expiration check job
def schedule_expiration_check():
    with app.app_context():
        check_subscription_expirations()

# Set up scheduler for daily expiration check
app.jinja_env.globals.update(schedule_expiration_check=schedule_expiration_check)

if __name__ == "__main__":
    socketio.run(app, debug=True)
