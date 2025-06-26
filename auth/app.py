from flask import Flask, Response, request, redirect, url_for, make_response, jsonify, render_template
import sys
from uuid import uuid4
from cryptography.fernet import Fernet 
import datetime
import pyotp
import os 

# sys.path.append('/home/ubuntu/apps/home-server/user') # add this if run outside docker (docker-compose)

from utils import dbconnection
from utils.user_sql import *
from utils.hash import create_new_device_hmac, check_device_hmac
try:
    import response
except ModuleNotFoundError:
    import auth.response as response
    print("response loaded")

DEBUG = True

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET")

def get_accepted_cookies(request):
    # To protect against DoS - with forcing the server to do large computations
    MAX_DEVICE_ID_LEN = 64
    MAX_HMAC_SECRET_LEN = 64

    if not ("device_id" in request.cookies.keys() and "hmac_secret" in request.cookies.keys()):
        return None, None

    device_id, hmac_secret = request.cookies["device_id"], request.cookies["hmac_secret"]
    if (len(device_id) > MAX_DEVICE_ID_LEN) or (len(hmac_secret) > MAX_HMAC_SECRET_LEN):
        return None, None

    return device_id, hmac_secret

@app.route("/login")
def login_device_html_route():
    device_id, hmac_secret = get_accepted_cookies(request)

    if device_id is None or hmac_secret is None:
        return render_template("login.html")

    device_id, hmac_secret = request.cookies["device_id"], request.cookies["hmac_secret"]

    user = get_user_from_device_id(device_id, db_conn_data=app.db_conn_data)

    if (user is None): 
        return render_template("login.html")

    return make_response(redirect(os.environ.get('login_redirect')))

@app.route("/device/add", methods=["POST"])
def add_device_route():
    device_id, hmac_secret = get_accepted_cookies(request)

    # If device already logged in
    if device_id is not None and hmac_secret is not None:
        return response.make_auth_error(401, "Invalid email or password")

    # If not correct json data sent 
    if not ("email" in request.json.keys() and "device_registration_code" in request.json.keys() and "device_type" in request.json.keys()):
        return response.make_auth_error(401, "Invalid email or password")

    user_email, totp_input, device_type = request.json["email"], request.json["device_registration_code"], request.json["device_type"]
    user = get_user_from_email(user_email)
    
    print(totp_input)

    # If user not found avoid faster computation and return 401
    if user is None:
        verify_user_TOTP_from_email("invalid_email", totp_input, db_conn_data=app.db_conn_data)
        return response.make_auth_error(401, "Invalid email or password")

    # Check valid totp
    if not verify_user_TOTP_from_email(user_email, totp_input, db_conn_data=app.db_conn_data):
        return response.make_auth_error(401, "Invalid email or password")
    
    # Generate and add new device
    device_id, hmac_secret, hmac_signature = create_new_device_hmac()
    add_device(device_id, user['UserID'], hmac_signature, device_type, app.db_conn_data)
    
    # Return valid response with set cookies 
    res = response.make_auth_valid()
    res.set_cookie('device_id', device_id, expires=datetime.datetime.now() + datetime.timedelta(days=int(os.environ.get("cookie_lifetime_days"))), domain=os.environ.get('cookie_domain'), secure=True, httponly=True, samesite='None')
    res.set_cookie('hmac_secret', hmac_secret, expires=datetime.datetime.now() + datetime.timedelta(days=int(os.environ.get("cookie_lifetime_days"))), secure=True, domain=os.environ.get('cookie_domain'), httponly=True, samesite='None')
    return res

@app.route("/verify/<service>")
def verify_service_route(service):
    # check authorization header is added 
    if (request.authorization is None):
        return response.make_auth_error(401, "Requiring service Authorization")

    # verify the authorization - service token
    is_valid_service_token, service_id = verify_service_token(service, request.authorization.token, db_conn_data=app.db_conn_data)
    if not is_valid_service_token:
        return response.make_auth_error(401, f"Could not verify service")
    
    # Check necessary cookies are present 
    device_id, hmac_secret = get_accepted_cookies(request)
    if device_id is None or hmac_secret is None:
        return response.make_auth_error(401, "Invalid device_id or hmac_secret")

    # verify the device signature    
    if not (verify_device(device_id, hmac_secret, db_conn_data=app.db_conn_data)):
        return response.make_auth_error(401, f"Could not verify Device")
    
    # Get User and UserServiceToken
    user = get_user_from_device_id(device_id, db_conn_data=app.db_conn_data)
    user_service_token = get_user_service_token_from_device(device_id, service, db_conn_data=app.db_conn_data)

    # Check User is connected the service
    if user_service_token is None:
        if user["Role"] == "admin":
            # If admin does not yet have a userService -> add user access
            user_service_token = add_user_service(user["UserID"], service_id, db_conn_data=app.db_conn_data)
        else:
            # If user does not have permissions to use service
            return response.make_auth_error(401, f"User does not have sufficient permissions")

    # Add UserRole to response data
    user_service_token["UserRole"] = user["Role"]
    
    # Update device and service last login
    with dbconnection(app.db_conn_data) as cursor:
        cursor.execute("update Device set LastLogin = %s where DeviceID = %s", (datetime.datetime.now(), device_id))
        cursor.execute("update UserService set LastLogin = %s where UserID = %s", (datetime.datetime.now(), user["UserID"]))
    
    # Return valid response Only data the service needs to exclude ServiceID and UserID to actually keep user info from services
    return response.make_verify_valid({"UserServiceToken": user_service_token["UserServiceToken"], "UserRole": user_service_token["UserRole"]})

if __name__ == "__main__":
    # Propagate exceptions for easier debugging
    app.config["PROPAGATE_EXCEPTIONS"] = True

    # When executed as main - connect to database based on environment variables
    app.db_conn_data = {
        "host":os.environ.get("DB_HOST"),
        "user":os.environ.get("DB_USER"),
        "port":os.environ.get("DB_PORT"),
        "password":os.environ.get("DB_PASSWORD"),
        "database":os.environ.get("MYSQL_DATABASE")
    }

    # Run app on for all hosts (if from docker-compose -> only internal through nginx)
    app.run(host="0.0.0.0",debug = DEBUG)
