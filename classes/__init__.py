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

    #login
    from .services.loginAuth.loginView import loginView
    #employee data
    from .services.EmployeeData.employeeDataView import employeeDataView
    #timesheet
    from .services.timesheet.routes import timesheet_bp
    from .services.timesheet.manager.routes import manager_timesheet_bp
    from .services.timesheet.employee.routes import employee_timesheet_bp
    #salespipeline
    from .services.salesPipeline.salesPipelineView import salesPipelineView
    #contract Renewal
    from .services.contractRenewal.ContractView import contract_renewal
    #projects
    from .services.projectManager.routes import project_manager_bp
    #admin page
    from .services.AdminPage.adminView import adminView


    #register the routes
    app.register_blueprint(loginView)
    app.register_blueprint(employeeDataView)
    app.register_blueprint(timesheet_bp)
    app.register_blueprint(manager_timesheet_bp)
    app.register_blueprint(employee_timesheet_bp)
    app.register_blueprint(salesPipelineView)
    app.register_blueprint(contract_renewal)
    app.register_blueprint(project_manager_bp)
    app.register_blueprint(adminView)

    return app