#helps to convert this folder into a package to import 
#whatever in this file will run automatically when the folder is imported

from flask import Flask

from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())
secret_key = os.environ.get("SECRET_KEY")

def create_app():
    app = Flask(__name__)
    #used to encrypt or secure the cookies in the session data of app
    app.config['SECRET KEY'] = secret_key 

    #import the routes
    from .loginView import loginView
    from .employeeDataView import employeeDataView

    #register the routes
    app.register_blueprint(loginView)
    app.register_blueprint(employeeDataView)

    return app