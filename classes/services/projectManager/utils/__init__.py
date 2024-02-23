from datetime import datetime
import json
from bson import ObjectId
from flask import jsonify, make_response
from pymongo import MongoClient

from ...connectors.dbConnector import dbConnectCheck, get_WorkAccount
from ...timesheet.utils import userType
from ...workbase.models import Task, Team, Project, Job

# Function to determine the user type based on the account ID
def fetch_projects(account_uuid, user_type):
    try: 
        # Check the connection to the MongoDB server
        client = dbConnectCheck()
        
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
            work_pipeline = [
                    {"$lookup": {"from": "Projects","localField": "_id","foreignField": "managerID","as": "projects"}},
                    {"$match":  {"projects": {"$ne": []}}},
                    {"$lookup": {"from": "Tasks","localField": "projects._id","foreignField": "projectID","as": "tasks"}},
                    {"$lookup": {"from": "Assignments","localField": "tasks._id","foreignField": "taskID","as": "assignments"}},
                    {"$lookup": {"from": "Members","localField": "assignments.assignedTo","foreignField": "_id","as": "members"}},
                    {"$lookup": {"from": "Teams","localField": "projects._id","foreignField": "projectID","as": "teams"}},
                    {"$lookup": {"from": "Members","localField": "teams._id","foreignField": "teamID","as": "teamMembers"}},
                    {"$addFields": {
                        "projects": {
                            "$map": {
                            "input": "$projects",
                            "as": "project",
                            "in": {
                                "$mergeObjects": [
                                "$$project",
                                {
                                    "tasks": {
                                    "$map": {
                                        "input": {
                                        "$filter": {
                                            "input": "$tasks",
                                            "as": "task",
                                            "cond": { "$eq": ["$$task.projectID", "$$project._id"] }
                                        }
                                        },
                                        "as": "task",
                                        "in": {
                                        "$mergeObjects": [
                                            "$$task",
                                            {
                                            "assignments": {
                                                "$map": {
                                                "input": {
                                                    "$filter": {
                                                    "input": "$assignments",
                                                    "as": "assignment",
                                                    "cond": { "$eq": ["$$assignment.taskID", "$$task._id"] }
                                                    }
                                                },
                                                "as": "assignment",
                                                "in": {
                                                    "$mergeObjects": [
                                                    "$$assignment",
                                                    {
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
                                                                    "cond": { "$eq": ["$$member._id", "$$assignedToId"] }
                                                                    }
                                                                }
                                                                },
                                                                "in": { "$arrayElemAt": ["$$member", 0] }
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
                                            "cond": { "$eq": ["$$team.projectID", "$$project._id"] }
                                        }
                                        },
                                        "as": "team",
                                        "in": {
                                        "$mergeObjects": [
                                            "$$team",
                                            {
                                            "teamMembers": {
                                                "$filter": {
                                                "input": "$teamMembers",
                                                "as": "teamMember",
                                                "cond": { "$eq": ["$$teamMember.teamID", "$$team._id"] }
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
                    {
                        "$project": {
                        "_id": 0,
                        "managerID": "$_id",
                        "projects": 1
                        }
                    },
                    {
                        "$match": {
                        "managerID": ObjectId(manager_id)
                        }
                    }
                    ]

            assignee_pipeline=[
            { "$group": {
                "_id": "$assignedBy",
                "Assignee": {
                    "$push": {
                    "_id": "$_id",
                    "name": "$name",
                    "assignmentInstances": "$assignmentInstances"
                    }
                }
                }
            },
            {
                "$project": {
                "_id": 0,
                "managerID": "$_id",
                "Assignee": 1
                }
            },
            {"$match": {"managerID": ObjectId(manager_id)}},
            ]

            manager_data = list(client.WorkBaseDB.Members.aggregate(work_pipeline))
            assignee_data = list(client.TimesheetDB.AssignmentGroup.aggregate(assignee_pipeline))
            # Check if manager data is empty
            if not manager_data:
                return make_response(jsonify({"message": "No Data here yet"}), 200)
            # if not assignee_data:
            #     return make_response(jsonify({"message": "No Data here yet"}), 200)
            # Merge the manager data and assignee data on managerID
            for i in range(len(manager_data)):
                for j in range(len(assignee_data)):
                    if manager_data[i]['managerID'] == assignee_data[j]['managerID']:
                        manager_data[i]['Assignee'] = assignee_data[j]['Assignee']
                        # pop managerID field
                        manager_data[i].pop('managerID')

            # Convert the employee_sheets cursor object to a JSON object
            manager_json = json.dumps(manager_data, default=str)
            manager_data_results = json.loads(manager_json)
            # Return the JSON response
            return make_response(jsonify({"managerProjectData": manager_data_results}), 200)          





                # if project_list:
                #     # Return the project list
                #     return make_response(jsonify({"projects": project_list}), 200)
                # else:
                #     # If the project list is empty, return the error response
                #     return make_response(jsonify({"error": "No projects found"}), 404)
            
            
            
            # # If the user type is 'employee'
            # elif user_type == "employee":
            #     # Get all the projects from the collection
            #     project_list = list(projects.find({"account_id": ObjectId(account_id)}))
            #     # If the project list is not empty
            #     if project_list:
            #         # Return the project list
            #         return make_response(jsonify({"projects": project_list}), 200)
            #     else:
            #         # If the project list is empty, return the error response
            #         return make_response(jsonify({"error": "No projects found"}), 404)
            # else:
            #     # If the user type is neither 'admin' nor 'user', return the error response
            #     return make_response(jsonify({"error": "Invalid user type"}), 400)

            
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
        account_id = verify.json['_id']
        # If the connection is successful
        if isinstance(client, MongoClient):
            # Get the 'name' field from the project data
            project_name = project_data.get('name')
            # Get the 'description' field from the project data
            project_description = project_data.get('description')
            # Get the 'manager_id' field from the project data
            project_manager_id = project_data.get('managerID')
            # Get the 'status' field from the project data
            project_status = project_data.get('status')
            # Get the 'budget' field from the project data
            project_budget = project_data.get('budget')
            # Get the 'actual_cost' field from the project data
            project_actual_cost = project_data.get('actual_cost')
            # Get the 'planned_cost' field from the project data
            project_planned_cost = project_data.get('planned_cost')
            # Get the 'created_at' field from the project data
            project_created_at = datetime.now()

            # create the project
            project = Project(name=project_name, description=project_description, managerID=project_manager_id, status=project_status, budget=project_budget, actual_cost=project_actual_cost, planned_cost=project_planned_cost, created_at=project_created_at, created_by=account_id)
            # Insert the project into the collection
            project_id = client.WorkBaseDB.Projects.insert_one(project)
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
            project_id = client.WorkBaseDB.Teams.insert_one(team)
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
            jobs = task_data.get('joblist')
            # Get the 'description' field from the task data
            description = task_data.get('description')
            # Get the 'completionStatus' field from the task data
            completion_status = task_data.get('completionStatus')

            # create joblist object from list of jobs
            joblist = []
            for job in jobs:
                joblist.append(Job(job=job['job'], deadline=job['deadline'], activeStatus=job['activeStatus']))

            # create the task
            task = Task(name=task_name, projectID=project_id, billable=billable, deadline=deadline, joblist=joblist, description=description, completionStatus=completion_status)
            # Insert the task into the collection
            project_id = client.WorkBaseDB.Tasks.insert_one(task)
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