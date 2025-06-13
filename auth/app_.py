from flask import Flask, Response, request, redirect, url_for, make_response, jsonify, render_template
import sys
from uuid import uuid4
import datetime

# sys.path.append('/home/ubuntu/apps/home-server/user') # add this if run outside docker (docker-compose)

from utils import users

DEBUG = False
LOGINTRIES = 1

SERVICES = ["spotify", "movies", "books"]

app = Flask(__name__)
app.secret_key = str(uuid4())

@app.route("/device/generate_key", methods=["POST"])
def generate_device_key():
    global LOGINTRIES

    device_id = request.json["device_id"]
    _, user = users.try_get_user_by_device_id(device_id)

    if user is None:
        return "UNAUTHORIZED", 401
    users.add_registration_code(device_id)
    LOGINTRIES = 3

    return "SUCCESS", 200

@app.route("/login")
def login_device_html():
    # if user is already logged in
    try: 
        device_id = request.cookies.get('device_id')
        _, user = users.try_get_user_by_device_id(device_id)
        if user is None:
            raise Exception("Invalid Device Id!")
    except:
        return render_template("login.html")
    # return "HI", 200
    return make_response(redirect("/"))

@app.route("/device/add", methods=["POST"])
def login_device():
    global LOGINTRIES
    device_registration_code = request.json["device_registration_code"]
    _, user = users.try_get_user_by_device_registration_code(device_registration_code)

    if LOGINTRIES < 1:
        return "UNAUTHORIZED", 401
    if user is None:
        LOGINTRIES -= 1
        return "UNAUTHORIZED", 401

    device_name = request.json["device_name"]
    new_device_id = users.add_device(device_name, user["id"])

    response = make_response(redirect("/"))
    response.set_cookie('device_id', new_device_id, expires=datetime.datetime.now() + datetime.timedelta(days=365), secure=True)
    return response
 
#   response.set_cookie('device_id', new_device_id, domain="192.168.7.100", expires=datetime.datetime.now() + datetime.timedelta(days=365))
#   response.set_cookie('device_id', new_device_id, domain="84.138.84.238", expires=datetime.datetime.now() + datetime.timedelta(days=365))
#
#     res = jsonify({
#         # "id": request.json["id"],
#         "new_device_id": new_device_id
#     })
#     return res, 200
    

@app.route("/verify/<service>")
def verify_cookie(service):
    if not ("device_key" in request.cookies.keys()):# or request.cookies["device_id"] == "":
        return "NOT FOUND", 404

    _, user = users.try_get_user_by_device_id(request.cookies["device_key"])

    if user is None:
        return "UNAUTHORIZED", 404
    if (not service in user["services"]) and (not user["admin"]):
        return "SERVICE FORBIDDEN", 403

    return "SUCCESS", 200

# @app.route("/verifhttps://84.238.84.138/media/admin/updatemediay/<service>/<device_id>")
# DEPRECATED 
# def verify_token(service, device_id):
    # if "device_key" in request.cookies.keys():
        # device_id = request.cookies["device_key"]

    # print(device_id)

    # _, user = users.try_get_user_by_device_id(device_id)

    # if user is None:
        # return "UNAUTHORIZED", 401
    # if (not service in user["services"]) and (not user["admin"]):
        # return "SERVICE FORBIDDEN", 403

    # return "SUCCESS", 200

@app.route("/isadmin")
def verify_token():
    if "device_key" in request.cookies.keys():
        device_id = request.cookies["device_key"]

    _, user = users.try_get_user_by_device_id(device_id)

    if (user is None) or (not user["admin"]):
        return "UNAUTHORIZED", 401

    return "SUCCESS", 200

@app.route("/verify_ip/<service>/<remote_addr>")
def verify_network(service, remote_addr):
    if not ("192.168.7." in remote_addr):
        return "UNAUTHORIZED", 401
    return "UNAUTHORIZED", 401
    
    # TODO - forward ip correctly - now all are 192.168.7.100
    # seems like nginx does not forward ip correctly so all ip's are verified for now 
    # return "SUCCESS", 200


@app.route("/user/get/<token>")
def get_username(access_token):
    _, user = users.try_get_user_by_device_id(access_token)

    if user is None:
        return "UNAUTHORIZED", 401

    res = jsonify({
        "name" : user["name"]

    })
    return res, 200

if __name__ == "__main__":
    
    app.run(host="0.0.0.0",debug = DEBUG)
