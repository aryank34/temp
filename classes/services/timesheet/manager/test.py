# api/timesheet/manager/modules.py
from flask import Flask,jsonify, request
from flask_restful import Resource, Api, reqparse, abort
from models import ManagerSheets, Day

# Create the Flask application
app = Flask(__name__)
api=Api(app)

####################################################
video_put_args = reqparse.RequestParser()
video_put_args.add_argument("name", type=str, help="Name of the video is required", required=True)
video_put_args.add_argument("views", type=int, help="views of video", required=True)
video_put_args.add_argument("likes", type=int, help="likes on video", required=True)

videos = {}

def abort_if_video_id_doesnt_exist(video_id):
    if video_id not in videos:
        abort(404, message="Video id is not valid...")

def abort_if_video_id_exists(video_id):
    if video_id in videos:
        abort(409, message="Video already exists with that ID...")

class Video(Resource):
    def get(self, video_id):
        abort_if_video_id_doesnt_exist(video_id)
        return videos[video_id]
    
    def get1(self):
        return videos
    
    def put(self, video_id):
        abort_if_video_id_exists(video_id)
        args = video_put_args.parse_args()
        videos[video_id] = args
        return videos[video_id], 201
    
    def delete(self, video_id):
        abort_if_video_id_doesnt_exist(video_id)
        del videos[video_id]
        return '', 204

api.add_resource(Video, "/video/<int:video_id>")
#########################################################


def create_manager_sheet():
    if request.method == 'POST':
        data = request.json
        work_days = {
            'mon': Day(**data["work_days"]["mon"]),
            'tue': Day(**data["work_days"]["tue"]),
            'wed': Day(**data["work_days"]["wed"]),
            'thu': Day(**data["work_days"]["thu"]),
            'fri': Day(**data["work_days"]["fri"]),
            'sat': Day(**data["work_days"]["sat"]),
            'sun': Day(**data["work_days"]["sun"]),
        }
        new_manager_sheet = ManagerSheets(
            projectID=data["projectID"],
            startDate=data["startDate"],
            endDate=data["endDate"],
            workDay=work_days,
            description=data["description"],
            status=data["status"],
            assignGroupID=data["assignGroupID"]
        )
        new_manager_sheet.save()
        return jsonify({"message": "Manager sheet created successfully."}), 201

def get_draft_timesheets():
    # Implement logic to retrieve draft timesheets
    # Return the result
    pass

def assign_timesheet(data):
    # Implement logic to assign timesheet to employees
    # Validate data and update the database
    # Return the result
    pass
