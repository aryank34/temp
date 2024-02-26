from datetime import datetime
import json
from bson import ObjectId
from flask import jsonify, make_response
from pymongo import MongoClient

from ...connectors.dbConnector import dbConnectCheck, get_WorkAccount, verify_attribute
from ...timesheet.utils import userType
from ...workbase.models import Assignment, Task, Team, Project, Job
from ...timesheet.models import AssignmentGroup, AssignmentInstance
# Function to determine the user type based on the account ID
def fetch_projects(account_uuid=None, user_type= None, superAdmin=False):
    try: 
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        
        if account_uuid is not None and user_type is not None:
            verify = get_WorkAccount(client, account_uuid)
            if not verify.status_code == 200:
                # If the connection fails, return the error response
                return verify
            account_id = verify.json['_id']

            # If the connection is successful
            if isinstance(client, MongoClient):
                # If the user type is 'manager'
                if user_type == "manager":
                    manager_id = account_id
                    # Get all the projects from the collection

                    superAdmin_pipeline = [
                        {"$lookup": {"from": "Projects","localField": "_id","foreignField": "managerID","as": "projects"}},
                            {"$match": {"projects": {"$ne": []}}},
                        {"$lookup": {"from": "AssignmentGroup","localField": "projects._id","foreignField": "projectID","as": "Assignee"}},
                        {"$lookup": {"from": "Assignments","localField": "Assignee.assignmentInstances.assignmentID","foreignField": "_id","as": "assignments"}},
                        {"$lookup": {"from": "Members","localField": "assignments.assignedTo","foreignField": "_id","as": "members"}},
                        {"$lookup": {"from": "Tasks","localField": "assignments.taskID","foreignField": "_id","as": "tasks"}},
                        {"$lookup": {"from": "Teams","localField": "projects._id","foreignField": "projectID","as": "teams"}},
                        {"$lookup": {"from": "Members","localField": "teams._id","foreignField": "teamID","as": "teamMembers"}},
                        {"$project": {"teamID": 0,"role": 0,"employeeDataID": 0,"name": 0,"projects.managerID": 0,"Assignee.assignedBy": 0,
                                    "Assignee.assignmentInstances.assignDate": 0,"assignments.projectID": 0,"assignments.assignedBy": 0,
                                    "members.employeeDataID": 0,"teamMembers.employeeDataID": 0,"members.teamID": 0,"tasks.projectID": 0,
                                    "tasks.deadline": 0,"tasks.joblist": 0,"tasks.completionStatus": 0}},
                        {"$project": {"_id": 1,"projects": 1,"assignments": 1,"members": 1,"tasks": 1,"teams": 1,"teamMembers":1,
                                    "Assignee": {"$map": {"input": "$Assignee",
                                                                    "as": "group",
                                                                    "in": {"_id": "$$group._id",
                                                                        "name": "$$group.name",
                                                                        "assignmentInstances": {
                                                                            "$map": {"input": "$$group.assignmentInstances",
                                                                            "as": "instance",
                                                                            "in": "$$instance.assignmentID"}},
                                                                            "projectID": "$$group.projectID"}}}}},
                        {"$addFields": {
                            "projects": {
                                "$map": {
                                "input": "$projects",
                                "as": "project",
                                "in": {
                                    "$mergeObjects": [
                                    "$$project",
                                    {
                                        "Assignee": {
                                        "$map": {
                                            "input": {
                                            "$filter": {
                                                "input": "$Assignee",
                                                "as": "group",
                                                "cond": {"$eq": ["$$group.projectID", "$$project._id"]}
                                            }
                                            },
                                            "as": "group",
                                            "in": {
                                            "$mergeObjects": [
                                                "$$group",
                                                {
                                                "assignment": {
                                                    "$map": {
                                                    "input": {
                                                        "$filter": {
                                                        "input": "$assignments",
                                                        "as": "assignment",
                                                        "cond": {"$in": ["$$assignment._id", "$$group.assignmentInstances"]}
                                                        }
                                                    },
                                                    "as": "assignment",
                                                    "in": {
                                                        "$mergeObjects": [
                                                        "$$assignment",
                                                        {
                                                            "tasks": {
                                                            "$map": {
                                                                "input": {
                                                                "$filter": {
                                                                    "input": "$tasks",
                                                                    "as": "task",
                                                                    "cond": {"$eq": ["$$assignment.taskID", "$$task._id"]}
                                                                }
                                                                },
                                                                "as": "task",
                                                                "in": "$$task"
                                                            }
                                                            },
                                                            "assignedTo": {
                                                            "$map": {
                                                                "input": "$$assignment.assignedTo",
                                                                "as": "assignedToId",
                                                                "in": {
                                                                "$let": {
                                                                    "vars": {
                                                                    "member": {
                                                                        "$filter": {
                                                                        "input": "$members",
                                                                        "as": "member",
                                                                        "cond": {"$eq": ["$$member._id", "$$assignedToId"]}
                                                                        }
                                                                    }
                                                                    },
                                                                    "in": {"$arrayElemAt": ["$$member", 0]}
                                                                }
                                                                }
                                                            }
                                                            }
                                                        }
                                                        ]
                                                    }
                                                    }
                                                }
                                                }
                                            ]
                                            }
                                        }
                                        },
                                        "teams": {
                                        "$map": {
                                            "input": {
                                            "$filter": {
                                                "input": "$teams",
                                                "as": "team",
                                                "cond": {"$eq": ["$$team.projectID", "$$project._id"]}
                                            }
                                            },
                                            "as": "team",
                                            "in": {
                                            "$mergeObjects": [
                                                "$$team",
                                                {

                                                "teamLead": {
                                                    "$filter": {
                                                    "input": "$teamMembers",
                                                    "as": "lead",
                                                    "cond": {"$eq": ["$$lead._id", "$$team.leadID"]}
                                                    }
                                                },
                                                "teamMembers": {
                                                    "$filter": {
                                                    "input": "$teamMembers",
                                                    "as": "teamMember",
                                                    "cond": {"$eq": ["$$teamMember.teamID", "$$team._id"]}
                                                    }
                                                }
                                                }
                                            ]
                                            }
                                        }
                                        }
                                    }
                                    ]
                                }
                                }
                            }
                            }
                        },
                        {"$project": {"_id": 0,"managerID": "$_id","Projects": "$projects",}},
                        {"$project": {"Projects.teams.projectID": 0,"Projects.teams.leadID": 0,"Projects.teams.teamLead.teamID": 0,"Projects.teams.teamLead.role": 0,"Projects.teams.teamMembers.teamID": 0,
                                    "Projects.Assignee.assignmentInstances": 0,"Projects.Assignee.projectID": 0,"Projects.Assignee.assignment.taskID": 0}},
                        ]
                        
                    manager_pipeline = superAdmin_pipeline.copy()
                    manager_pipeline.append({"$match": {"managerID": ObjectId(manager_id)}})

                    project_data = []
                    if superAdmin:
                        project_data = list(client.WorkBaseDB.Members.aggregate(superAdmin_pipeline))
                    else:
                        project_data = list(client.WorkBaseDB.Members.aggregate(manager_pipeline))
                    
                    # return make_response(jsonify({"superAdmin": superAdmin,"list items": len(project_data)}), 200)
                    # Check if manager data is empty
                    if not project_data:
                        return make_response(jsonify({"message": "There is no Project here yet"}), 200)
            
                    # Convert the employee_sheets cursor object to a JSON object
                    project_json = json.dumps(project_data, default=str)
                    project_data_results = json.loads(project_json)
                    # Return the JSON response
                    return make_response(jsonify({"managerProjectData": project_data_results}), 200)          
                    
                # If the user type is 'employee'
                elif user_type == "employee":
                    # Get all the projects from the collection
                    return make_response(jsonify({"error": "Projects for Employees COMING SOON..."}), 404)
                    project_list = list(projects.find({"account_id": ObjectId(account_id)}))
                    # If the project list is not empty
                    if project_list:
                        # Return the project list
                        return make_response(jsonify({"projects": project_list}), 200)
                    else:
                        # If the project list is empty, return the error response
                        return make_response(jsonify({"error": "No projects found"}), 404)
                else:
                    # If the user type is neither 'admin' nor 'user', return the error response
                    return make_response(jsonify({"error": "Invalid user type"}), 400)

                
            else:
                # If the connection fails, return the error response
                return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
        else:
            # If the account ID is not provided, return the error response
            return make_response(jsonify({"error": "Account ID is required"}), 400)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def fetch_organization_members(superAdmin_uuid):
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        verify = get_WorkAccount(client, superAdmin_uuid)
        if not verify.status_code == 200:
            # If the connection fails, return the error response
            return verify
        account_id = verify.json['_id']

        # If the connection is successful
        if isinstance(client, MongoClient):
            # build a pipeline to retrieve all members from database
            members_pipeline = [
                {"$project": {"_id": 1, "name": 1, "role": 1}},
                ]

            # Get all the members from the collection
            members = list(client.WorkBaseDB.Members.aggregate(members_pipeline))
            # If the members list is not empty
            if not members:
                # Return the members list
                return make_response(jsonify({"error": "No members found"}), 404)
            
            # sort members according to role
            members.sort(key=lambda x: x['role'])

            # Convert the manager_sheets cursor object to a JSON object
            members_json = json.dumps(members, default=str)
            # Parse the JSON string into a Python data structure
            members_data = json.loads(members_json)

            # Return the JSON response as managerSheets, preserve the output format
            return make_response(jsonify({"members": members_data}), 200)
            
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)
    
def create_projects(admin_uuid, project_data):
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        verify = get_WorkAccount(client, admin_uuid)
        if not verify.status_code == 200:
            # If the connection fails, return the error response
            return verify
        account_id = ObjectId(verify.json['_id'])
        # If the connection is successful
        if isinstance(client, MongoClient):
            # check if managerID is valid
            if project_data['managerID'] is not None:
                project_data['managerID'] = ObjectId(project_data['managerID'])
                verify = verify_attribute(collection=client.WorkBaseDB.Members, key="_id",attr_value=ObjectId(project_data['managerID']))
                if not verify:
                    return make_response(jsonify({"error": "Manager is not valid"}), 400)                    
            else:
                return make_response(jsonify({"error": "Manager data is required"}), 400)
            
            # check if project Name exists in payload
            if project_data['name'] is None:
                return make_response(jsonify({"error": "Project Name is required"}), 400)
            # check if project description exists in payload
            if project_data['description'] is None:
                return make_response(jsonify({"error": "Project Description is required"}), 400)
            
            # create the project
            project = Project(name=project_data['name'], description=project_data['description'], managerID=project_data['managerID'], status=project_data['status'], budget=project_data['budget'], actual_cost=project_data['actual_cost'], planned_cost=project_data['planned_cost'], created_by=account_id)
            # Insert the project into the collection
            project_id = client.WorkBaseDB.Projects.insert_one(project.to_dict())
            # return make_response(jsonify({"message": "Working"}), 200)
            # If the project is successfully created
            if project_id:
                # Return the success response
                return make_response(jsonify({"message": "Project created successfully"}), 201)
            else:
                # If the project creation fails, return the error response
                return make_response(jsonify({"error": "Failed to create project"}), 500)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)
            
def create_teams(admin_uuid, team_data):
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        verify = get_WorkAccount(client, admin_uuid)
        if not verify.status_code == 200:
            # If the connection fails, return the error response
            return verify
        account_id = verify.json['_id']

        # If the connection is successful
        if isinstance(client, MongoClient):
            # Get the 'name' field from the team data
            team_name = team_data.get('name')
            # Get the 'project_id' field from the team data
            project_id = team_data.get('projectID')
            # Get the 'lead_id' field from the team data
            lead_id = team_data.get('leadID')

            # create the team
            team = Team(name=team_name, projectID=project_id, leadID=lead_id)
            # Insert the team into the collection
            project_id = client.WorkBaseDB.Teams.insert_one(team.to_dict())
            # If the team is successfully created
            if project_id:
                # Return the success response
                return make_response(jsonify({"message": "team created successfully"}), 201)
            else:
                # If the team creation fails, return the error response
                return make_response(jsonify({"error": "Failed to create team"}), 500)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)
    
def create_tasks(manager_uuid, task_data):
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        verify = get_WorkAccount(client, manager_uuid)
        if not verify.status_code == 200:
            # If the connection fails, return the error response
            return verify
        account_id = verify.json['_id']

        # If the connection is successful
        if isinstance(client, MongoClient):
            # check if the manager account has access to the project for which task is being assigned
            # Get the 'project_id' field from the task data
            project_id = task_data.get('projectID')
            project = client.WorkBaseDB.Projects.find_one({"_id": ObjectId(project_id), "managerID": ObjectId(account_id)})
            if project is not None:
                return make_response(jsonify({"error": "Manager does not have access to the project"}), 403)
            # Get the 'name' field from the task data
            task_name = task_data.get('name')
            # Get the 'billable' field from the task data
            billable = task_data.get('billable')
            # Get the 'deadline' field from the task data
            deadline = task_data.get('deadline')
            # Get the 'joblist' field from the task data
            jobs = list(task_data.get('joblist'))
            # Get the 'description' field from the task data
            description = task_data.get('description')
            # Get the 'completionStatus' field from the task data
            completion_status = task_data.get('completionStatus')

            # create joblist object from list of jobs
            joblist = []
            for i in range(len(jobs)):
                joblist.append(Job(jobID=i+1,job=jobs[i]['job'], deadline=jobs[i]['deadline'], activeStatus=jobs[i]['activeStatus']))

            # create the task
            task = Task(name=task_name, projectID=project_id, billable=billable, deadline=deadline, joblist=joblist, description=description, completionStatus=completion_status)
            # Insert the task into the collection
            project_id = client.WorkBaseDB.Tasks.insert_one(task.to_dict())
            # If the task is successfully created
            if project_id:
                # Return the success response
                return make_response(jsonify({"message": "task created successfully"}), 201)
            else:
                # If the task creation fails, return the error response
                return make_response(jsonify({"error": "Failed to create task"}), 500)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def create_new_assignment_group(manager_uuid, assignment_details):
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        verify = get_WorkAccount(client, manager_uuid)
        if not verify.status_code == 200:
            # If the connection fails, return the error response
            return verify
        account_id = verify.json['_id']

        # If the connection is successful
        if isinstance(client, MongoClient):
            # check if the manager account has access to the project for which task is being assigned
            name = assignment_details.get('name')
            projectID = assignment_details.get('projectID')
            assignment_groups = assignment_details.get('assignment_groups')
            # check if the manager account has access to the assignment groups
            project = client.WorkBaseDB.Projects.find_one({"_id": ObjectId(projectID), "managerID": ObjectId(account_id)})
            if project is None:
                return make_response(jsonify({"error": "Manager does not have access to the project"}), 403)
            for assignment_member in assignment_groups:
                if not client.WorkBaseDB.Assignment.find_one({"_id": ObjectId(assignment_member), "projectID": ObjectId(projectID)}):
                    return make_response(jsonify({"error": "Assignment Group not found"}), 404)
                
            # check if manager has a AssignmentGroup for same project
            assignment_group = client.WorkBaseDB.AssignmentGroup.find_one({"assignedBy": ObjectId(account_id), "projectID": ObjectId(projectID)})
            if assignment_group is None:
                # create the assignment instances
                assignment_instances = [AssignmentInstance(assignDate=datetime.now(), assignmentGroupID=ObjectId(assignment_group)) for assignment_group in assignment_groups]
                # create the assignment group
                assignment_group = AssignmentGroup(name=name, assignedBy=account_id, projectID=projectID, assignmentInstances=assignment_instances)
                # Insert the assignment group into the collection
                client.TimesheetDB.AssignmentGroup.insert_one(assignment_group.to_dict())
                client.WorkBaseDB.AssignmentGroup.insert_one(assignment_group.to_dict())
            else:
                # check if any item in assignment_groups list is present at assignmentID of assignmentInstances list
                for instance in assignment_group['assignmentInstances']:
                    if instance['assignmentID'] in assignment_groups:
                        # remove the assignmentID from the assignment_groups list
                        assignment_groups.remove(instance['assignmentID'])
                if assignment_groups is None:
                    return make_response(jsonify({"message": "AssignmentGroup already exists"}), 200)
                for assignment_group in assignment_groups:
                    assignment_instance = AssignmentInstance(assignDate=datetime.now(), assignmentID=ObjectId(assignment_group))
                    # push this assignment instance to the assignmentInstances list in collection
                    result = client.TimesheetDB.AssignmentGroup.update_one({"_id": ObjectId(assignment_group['_id'])}, {"$push": {"assignmentInstances": assignment_instance}})
                    result = client.WorkBaseDB.AssignmentGroup.update_one({"_id": ObjectId(assignment_group['_id'])}, {"$push": {"assignmentInstances": assignment_instance}})
                    if result.modified_count == 0:
                        return make_response(jsonify({"error": "Failed to add assignment to AssignmentGroup"}), 500)
            # If the assignment group is successfully created
            return make_response(jsonify({"message": "Assignment Group created successfully"}), 201)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def create_new_task_assignment(manager_uuid, assignment_data):
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        verify = get_WorkAccount(client, manager_uuid)
        if not verify.status_code == 200:
            # If the connection fails, return the error response
            return verify
        account_id = verify.json['_id']

        # If the connection is successful
        if isinstance(client, MongoClient):
            # check if the manager account has access to the project for which task is being assigned
            # Get the 'project_id' and 'task_id' field from the assignment data
            project_id = assignment_data.get('projectID')
            task_id = assignment_data.get('taskID')
            project = client.WorkBaseDB.Projects.find_one({"_id": ObjectId(project_id), "managerID": ObjectId(account_id)})
            if project is None:
                return make_response(jsonify({"error": "Manager does not have access to the project"}), 403)
            task = client.WorkBaseDB.Tasks.find_one({"_id": ObjectId(task_id), "projectID": ObjectId(project_id)})
            if task is None:
                return make_response(jsonify({"error": "Task does not lie within the project"}), 403)

            # Get the 'name' of the assignment from the assignment data
            name = assignment_data.get('name')
            # Get the 'assigned_to' field from the assignment data
            assigned_to = assignment_data.get('assignedTo')
            # Get the 'assigned_by' field from the assignment data
            assigned_by = account_id

            # create the assignment
            assignment = Assignment(name=name, projectID=project_id, taskID=task_id, assignedTo=assigned_to, assignedBy=assigned_by)
            # Insert the assignment into the collection
            project_id = client.WorkBaseDB.Assignments.insert_one(assignment.to_dict())
            # If the assignment is successfully created
            if project_id:
                # Return the success response
                return make_response(jsonify({"message": "Assignment created successfully"}), 201)
            else:
                # If the assignment creation fails, return the error response
                return make_response(jsonify({"error": "Failed to create assignment"}), 500)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)

def edit_tasks(manager_uuid, task_data):
    try:
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        verify = get_WorkAccount(client, manager_uuid)
        if not verify.status_code == 200:
            # If the connection fails, return the error response
            return verify
        account_id = verify.json['_id']

        # If the connection is successful
        if isinstance(client, MongoClient):
            # check if the manager account has access to the project for which task is being edited
            # Get the 'project_id' and 'task_id' field from the task data
            task_id = task_data.get('taskID')
            task = client.WorkBaseDB.Tasks.find_one({{"_id": ObjectId(task_id)}})
            project = client.WorkBaseDB.Projects.find_one({"_id": ObjectId(task.get('projectID')), "managerID": ObjectId(account_id)})
            if project is None:
                return make_response(jsonify({"error": "Manager does not have access to the project"}), 403)

            # Get the task from the database
            task = client.WorkBaseDB.Tasks.find_one({"_id": ObjectId(task_id)})
            if task is None:
                return make_response(jsonify({"error": "Task not found"}), 404)

            # Get the 'name' field from the task data
            task_name = task_data.get('name')
            # Get the projectID field from the task data
            project_id = task_data.get('projectID')
            # Get the 'billable' field from the task data
            billable = task_data.get('billable')
            # Get the 'deadline' field from the task data
            deadline = task_data.get('deadline')
            # Get the 'joblist' field from the task data
            jobs = list(task_data.get('joblist'))
            # Get the 'description' field from the task data
            description = task_data.get('description')
            # Get the 'completionStatus' field from the task data
            completion_status = task_data.get('completionStatus')

            # update components
            joblist = []
            for i in range(len(jobs)):
                joblist.append(Job(jobID=i+1,job=jobs[i]['job'], deadline=jobs[i]['deadline'], activeStatus=jobs[i]['activeStatus']))




            # create the task
            # task = Task(name=task_name, projectID=project_id, billable=billable, deadline=deadline, joblist=joblist, description=description, completionStatus=completion_status)
            
            # # Update the task in the collection
            # result = client.WorkBaseDB.Tasks.update_one({"_id": ObjectId(task_id)}, {"$set": task})

            # # If the task is successfully updated
            # if result.modified_count > 0:
            #     # Return the success response
            #     return make_response(jsonify({"message": "Task updated successfully"}), 200)
            # else:
            #     # If the task update fails, return the error response
            #     return make_response(jsonify({"error": "Failed to update task"}), 500)
        else:
            # If the connection fails, return the error response
            return make_response(jsonify({"error": "Failed to connect to the MongoDB server"}), 500)
    except Exception as e:
        # If an error occurs, return the error response
        return make_response(jsonify({"error": str(e)}), 500)