from flask import make_response, request
from pymongo import MongoClient
#load and find the env file
from dotenv import load_dotenv, find_dotenv
import os
from pymongo.server_api import ServerApi
#jwt
import jwt

#regex
import re

#wraps- to prevent the overiding of function while checking the token
from functools import wraps

class tokenAuth:
    def __init__(self):
        try:
            load_dotenv(find_dotenv())
            mongo_host = os.environ.get("MONGO_HOST_prim")

            #python-mongo connection string
            uri = mongo_host
            client = MongoClient(uri, server_api=ServerApi('1'), UuidRepresentation="standard")

            
            self.endpointData = client.EmployeeDB.EndpointData

        except Exception as e:
            print("some error in authMongo connection with mongo")

    #create a decorator, that will run before every endpoint
    def token_auth(self, endpoint):
        def inner1(func):
            @wraps(func)
            def inner2(*args, **kwargs):
                Authorization = request.headers.get('Authorization')
                if re.match("^Bearer *([^ ]+) *$", Authorization, flags=0):
                    # token = Authorization.split(" ")[1]
                    # secret = os.environ.get('SECRET_KEY')
                    # algo = os.environ.get('ALGORITHM')
                    # #check the signature expiration of token that came from frontend
                    # try:
                    #     jwt_decoded = jwt.decode(token, secret, algorithms={algo})
                    # except jwt.ExpiredSignatureError:
                    #     return make_response({"ERROR":"Token Expired"}, 401)
                    # except jwt.DecodeError:
                    #     return make_response({"ERROR":"Wrong Token"}, 401)
                    try:
                        jwt_decoded = tokenAuth.token_decode(Authorization)
                    except jwt.ExpiredSignatureError:
                        return make_response({"ERROR":"Token Expired"}, 401)
                    except jwt.DecodeError:
                        return make_response({"ERROR":"Wrong Token"}, 401)                    

                    #extract role id from token - gives an array
                    # role_id = jwt_decoded['payload']['Role']['role_id'][0] #for now i have taken the first element
                    # print(role_id)

                    #get the array of roles from mongodb to check whether this user is allowed to access the route
                
                    # endpoint_access_role_ids = self.endpointData.find_one({"endPoint":endpoint},{"_id":0,"role_id":1})
                    # if endpoint_access_role_ids == None:
                    #     return make_response({"ERROR":"Unknown Endpoint"}, 404)
                    # # print(endpoint_access_role_ids)

                    # #check if the query returns something or not
                    # if (len(endpoint_access_role_ids)>0):
                    #     allowed_roles = endpoint_access_role_ids['role_id']
                    #     # print(allowed_roles)
                    #     if role_id in allowed_roles:
                    #         return func(*args, **kwargs)
                    #     else:
                    #         return make_response({"ERROR":"Invalid Role"}, 404)
                    # else:
                    #     return make_response({"ERROR":"Unknown Endpoint"}, 404)

                    # -----------------------------------------------------------------CORRECT BY MANNY and YOGI
                    endpoint_access_role_ids = self.endpointData.find_one({"endPoint":endpoint},{"_id":0,"role_id":1})    
                    if endpoint_access_role_ids == None:
                        return make_response({"ERROR":"Unknown Endpoint"}, 404)
                    #check if the query returns something or not
                    #extract role id from token - gives an array
                    role_id = jwt_decoded['payload']['Role']['role_id'] #all roles of the user
                    role_list = list(role_id)
                    if (len(endpoint_access_role_ids)>0):
                        allowed_roles = endpoint_access_role_ids['role_id']
                        # print(allowed_roles)
                        for roleID in role_list:
                            if roleID in allowed_roles:
                                return func(*args, **kwargs)
                        return make_response({"ERROR":"Invalid Role"}, 404)
                    else:
                        return make_response({"ERROR":"Unknown Endpoint"}, 404)
                else:
                    return make_response({"ERROR":"INVALID TOKEN"}, 401)
            return inner2
        return inner1
    
    def token_decode(auth_header):
        token = auth_header.split(" ")[1]
        secret = os.environ.get('SECRET_KEY')
        algo = os.environ.get('ALGORITHM')
        #check the signature expiration of token that came from frontend
        # print(jwt.decode(token, secret, algorithms={algo}))
        return jwt.decode(token, secret, algorithms={algo})
            
        