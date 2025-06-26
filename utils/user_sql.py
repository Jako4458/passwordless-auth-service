import uuid
import secrets
import pyotp
import json
import os
import sys
import time
from dotenv import load_dotenv
from uuid import uuid4
from cryptography.fernet import Fernet 

TOTP_encryption_key = os.environ.get("TOTP_ENCRYPTION_KEY").encode()


try:
    from utils.hash import sha512_string, check_hash, check_device_hmac
    from utils.dbconnection import dbconnection
except ModuleNotFoundError:
    from hash import sha512_string, check_hash, check_device_hmac
    from dbconnection import dbconnection


def user_input_db_con_data():
    db_conn_data = {}
    db_conn_data["host"] = input("host: ")
    db_conn_data["user"] = input("user: ")
    db_conn_data["port"] = input("port: ")
    db_conn_data["password"] = input("password: ")
    db_conn_data["database"] = input("database: ")

    return db_conn_data

def add_user_from_input(db_conn_data=None):
    userdata = {
        "Username" : input("username: "),
        "Email" : input("email: "),
        "Role" : "user",
        "TOTPSecret" : pyotp.random_base32()
    }

    return add_user(userdata, db_conn_data)

def add_user(userdata, db_conn_data=None):
    Username = userdata["Username"]
    Role = userdata["Role"]
    Email = userdata["Email"]
    TOTPSecret = userdata["TOTPSecret"]
    # TOTPSecretEncrypted = userdata["TOTPSecretEncrypted"]


    f = Fernet(TOTP_encryption_key)
    
    TOTPSecretEncrypted = f.encrypt(TOTPSecret.encode())

    with dbconnection(db_conn_data) as cursor:
        cursor.execute("INSERT INTO User (Username, Role, Email, TOTPSecretEncrypted) VALUES (%s, %s, %s, %s)",(Username, Role, Email, TOTPSecretEncrypted))

    return TOTPSecret, TOTPSecretEncrypted

def get_user_from_email(email, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from User where User.Email = %s", (email,))
        user = cursor.fetchone()
    return user 

def get_user_from_device_id(device_id, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select u.*  from User u join Device d on u.UserID = d.UserID where d.DeviceID = %s", (device_id,))
        user = cursor.fetchone()
    return user 
    
def delete_user_from_device_id(device_id, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("delete u from User u join Device d on u.UserID = d.UserID where d.DeviceID = %s", (device_id,))

def delete_user_from_id(user_id, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("delete u from User u where u.UserID = %s", (user_id,))

def verify_user_TOTP_from_email(user_email, totp_input, slide_window_sec=10, verification_time=None, db_conn_data=None):
    """return bool: true for valid TOTP"""
    user = try_get_user_from_email(user_email, db_conn_data)

    f = Fernet(TOTP_encryption_key)

    # If user is none, use a random TOTPsecret for the constant time check 
    if user is None:
        TOTP_secret = pyotp.random_base32()
    else: 
        TOTP_secret = f.decrypt(user["TOTPSecretEncrypted"].encode()).decode()
    
    totp = pyotp.TOTP(TOTP_secret)

    if verification_time is None:
        verification_time = time.time() 

    # Check with a slind window allow for codes to work a little after expiring - python short circuiting should avoid unnecessary computations 
    return totp.verify(totp_input, verification_time) or totp.verify(totp_input, verification_time - slide_window_sec)

def verify_device(device_id, hmac_secret, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from Device where DeviceID = %s",(device_id,))
        device = cursor.fetchone()
    # 
    if device is None:
        # timing Attack protection - Do random check_device_hmac to avoid speed-up with invalid device_id 
        check_device_hmac(secrets.token_hex(16), secrets.token_hex(16), "667f50b8f6e8b4c1d18a231259f83dba38c71d675c550c45cc1cc7927c2cef6c97992eea61a6bdd9edb2124051d5a4c0b8ca73794721951e818cd1e064c6deb3")
        return False
    return check_device_hmac(device_id, hmac_secret, device["DeviceHMACSignature"])

def add_service(service_name, db_conn_data=None):
    service_data = {
        "name": service_name,
        "token": str(uuid4())
    }
    service_data["hash_salt"], service_data["token_hash"] = sha512_string(service_data["token"])

    with dbconnection(db_conn_data) as cursor:
        cursor.execute("INSERT INTO Service (ServiceName, ServiceTokenHash, HashSalt) VALUES (%s, %s, %s)",(service_data["name"], service_data["token_hash"], service_data["hash_salt"]))

    return service_data

def delete_service_from_id(service_id, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("delete s from Service s where s.ServiceID = %s", (service_id,))

def verify_service_token(service_name, service_token, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from Service where ServiceName = %s",(service_name,))
        service = cursor.fetchone()

    if service is not None:
        if (check_hash(service_token, service["HashSalt"], service["ServiceTokenHash"])):
            return True, service["ServiceID"]
        else:
            return False, None

    # timing Attack protection - Do random check_hash to avoid speed-up with invalid service_name 
    check_hash("InvalidServiceToken", "InvalidHashSalt", "InvalidServiceTokenHash")
    return False, None

def add_user_service(user_id, service_id, db_conn_data=None):
    user_service_token = str(uuid4())

    f = Fernet(TOTP_encryption_key)
    
    user_service_token_encrypted = f.encrypt(user_service_token.encode())

    with dbconnection(db_conn_data) as cursor:
        cursor.execute("INSERT INTO UserService (UserID, ServiceID, UserServiceTokenEncrypted) VALUES (%s, %s, %s)",(user_id, service_id, user_service_token_encrypted))

    return {"UserID":user_id, "ServiceID": service_id,"UserServiceToken": user_service_token}

def delete_user_service_from_user_id_and_service_id(user_id, service_id, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("delete us from UserService us where us.UserID = %s and ServiceID = %s", (user_id, service_id))

def get_user_service_token_from_device(device_id, service_name, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select us.UserID, us.ServiceID, us.UserServiceTokenEncrypted from Device d join UserService us on d.UserID = us.UserID join Service s on us.ServiceID = s.ServiceID where d.DeviceID = %s and s.ServiceName = %s", (device_id, service_name))
        user_service = cursor.fetchone()
    if user_service is None:
        return None

    f = Fernet(TOTP_encryption_key)
    user_service["UserServiceToken"] = f.decrypt(user_service["UserServiceTokenEncrypted"].encode()).decode()

    return {"UserID": user_service['UserID'], "ServiceID": user_service['ServiceID'],"UserServiceToken": user_service["UserServiceToken"]}

def add_device(device_id, user_id, hmac_signature, device_type, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor: 
        cursor.execute("INSERT INTO Device (DeviceID, UserID, DeviceHMACSignature, DeviceType) VALUES (%s, %s, %s, %s)" ,(device_id, user_id, hmac_signature, device_type))
    return {"DeviceID": device_id, "UserID": user_id, "DeviceHMACSignature": hmac_signature, "DeviceType": device_type }

def delete_device_from_id(device_id, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("delete d from Device d where d.DeviceID = %s", (device_id,))

def get_all_users_as_list(db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from User")
        return cursor.fetchall()

def get_all_services_as_list(db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from Service")
        return cursor.fetchall()

def get_all_devices_as_list(db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from Device")
        return cursor.fetchall()

def get_all_user_services_as_list(db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from UserService")
        return cursor.fetchall()

def try_get_user_from_email(user_email, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from User where Email = %s",(user_email,))
        user = cursor.fetchone()
    return user

def try_get_user_from_id(user_id, db_conn_data=None):
    with dbconnection(db_conn_data) as cursor:
        cursor.execute("select * from User where UserID = %s",(user_id,))
        user = cursor.fetchone()
    return user

if __name__ == "__main__":
    print("cwd:", os.getcwd())
    print("__file__:", __file__)
    print("__name__:", __name__)

    if len(sys.argv) > 1:
        if "--test" in sys.argv:
            sys.argv.remove("--test")
            import unittest
            import user_test

            print("DEBUG: Loaded tests:")
            suite = unittest.defaultTestLoader.loadTestsFromModule(user_test)
            print(suite)

            unittest.TextTestRunner(verbosity=2).run(suite)
        if not "--run" in sys.argv:
            exit()

    db_conn_data = {
        "host":"127.0.0.1",
        "port":3307,
        "user":"testuser",
        "password":"testpass",
        "database":"testdb"
    }

    add_user_from_input_with_TOTP_printed(db_conn_data)
    # print(try_get_all_users_as_list())
    # print(try_get_user_from_id(1))
    # print(try_get_user_from_device_key("87fec75b86a920d517c67547c441e5cf"))

