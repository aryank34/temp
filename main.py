#to run the server

#this file will import the classes package, can __inti__.py file will automatically run and create an app

from classes import create_app

#allow CORS and give the frontend address to become the whitelist
from flask_cors import CORS

#load dotenv
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

frontend_url = os.environ.get("FRONTEND")

app = create_app()

# give * for allowing all the urls, give frontend url in production
# CORS(app, origins={frontend_url})
CORS(app, origins="*")

if __name__ == '__main__':
    app.run(debug = True)