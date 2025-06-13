import time
import pyotp
import os 

from testcontainers.mysql import MySqlContainer
import unittest 
from unittest.mock import patch

import utils.user_sql as user_sql
import auth.app as flask_app
from utils.dbconnection import dbconnection

class UserTesting(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.DEBUG = False
        self.flask_app = flask_app.app#.test_client()
        

    def setUp(self):
        """NOTE: IF ANYTHING IN HERE BREAKS EVEN A VAR NOT FOUND ITS LIKELY TO CAUSE A:
            docker.errors.APIError: 500 Server Error for http+docker://localhost/v1.47/containers/c336395e06481d65b4cc710147bdbf598ea122e28100d7a2712fbcf7a3d6d6f9/start: Internal Server Error ("driver failed programming external connectivity on endpoint nice_lumiere (5795b6ae2571b2971aafed2c47de9b8d7736d476b5ee1b98b86b26da68f9e996): Bind for 0.0.0.0:3307 failed: port is already allocated")
        """
        
        self.db_conn_data = {
            "user": "test",
            "password": "test",
            "database": "test"
        }


        self.container = MySqlContainer("mysql:8.0").with_bind_ports(3306, 3307) \
            .with_env("MYSQL_ROOT_PASSWORD", "root") \
            .with_env("MYSQL_DATABASE", self.db_conn_data["database"])   \
            .with_env("MYSQL_USER", self.db_conn_data["user"])       \
            .with_env("MYSQL_PASSWORD", self.db_conn_data["password"])
        # self.container._connect_timeout = 300  # Increase timeout to 5 minutes
        try: 
            self.container.start()
        except Exception as e:
            raise RuntimeError(f"Failed in setup: Look at first test Error!")

        try: 
            # self.addCleanup(self.container.stop)
            if self.DEBUG: print(self.container.get_logs())

            if self.DEBUG: print("setup 1/2")
            self.db_conn_data["host"] = self.container.get_container_host_ip()
            if self.DEBUG: print("setup 2/2")
            self.db_conn_data["port"] = self.container.get_exposed_port(3306)
            self.flask_app.db_conn_data = self.db_conn_data
            self.flask_app = self.flask_app.test_client()
            if self.DEBUG: print("setup complete")
            
            # self._load_sql_file("../mysqldb/00-setup.sql")
            self._load_sql_file("mysqldb/01-createUserTable.sql")
            self._load_sql_file("mysqldb/02-createDeviceTable.sql")
            self._load_sql_file("mysqldb/03-createServiceTable.sql")
            self._load_sql_file("mysqldb/04-createUserServiceTable.sql")
            # self._load_sql_file("../mysqldb/05-addRoles.sql")
            # self._load_sql_file("../mysqldb/06-addUsers.sql")
            self._load_sql_file("mysqldb/99-populate_testing_data.sql")
        except Exception as e:
            # self.container.stop()
            print(f"FAILED IN SETUP {e}")
            raise e

    def tearDown(self):
       self.container.stop()
    
    def _load_sql_file(self, filepath):
        if self.DEBUG: print(f"loading {filepath}")
        with open(filepath, "r") as f:
            sql = f.read()
        # try:
            # with open(filepath, "r") as f:
                # sql = f.read()
        # except Exception:
            # raise Exception(f"Failed reading file '{filepath}'")

        try:
            with dbconnection(self.db_conn_data) as cursor:
                for stmt in filter(None, map(str.strip, sql.split(";"))):
                    cursor.execute(stmt)
        except Exception:
            raise Exception(f"Failed executing '{filepath}'")

##############################################################

    def test_create_user(self):
        from cryptography.fernet import Fernet 

        userdata = {
            "Username" : "username",
            "Email" : "email",
            "Role" : "user",
            "TOTPSecret" : "TEST-STRING"
        }
        
        user_sql.add_user(userdata, self.db_conn_data)
        
        # assert user has not been added to db
        with dbconnection(self.db_conn_data) as cursor:
            cursor.execute("SELECT * FROM User WHERE Username = %s", (userdata["Username"],))
            row = cursor.fetchone()
            assert row is not None, "User was not added to the database"

            # Test correct load storage in db
            for key,val in userdata.items():
                if key == "TOTPSecret":
                    continue
                assert row[key] == val , f"Expected row[{key}] to be '{val}', got '{row['key']}'"

            # Test encryption
            
            assert row["TOTPSecretEncrypted"] != userdata["TOTPSecret"] , f"Expected TOTPSecret to be encrypted!'"
            assert Fernet(os.environ.get("TOTP_ENCRYPTION_KEY").encode()).decrypt(row["TOTPSecretEncrypted"].encode()).decode() == userdata["TOTPSecret"] , f"Expected TOTPSecret to be encrypted properly!'"

    def test_delete_user_from_device_id(self):
        # ('dev-002', 2, 'HMAC5678ALICE', NOW());
        User_id_to_delete = 2
        device_id = "88039525d4f12b8fc4e0c4fc84fd4db4"
        user_sql.delete_user_from_device_id(device_id, self.db_conn_data)
        
        # assert user has not been added to db
        with dbconnection(self.db_conn_data) as cursor:
            cursor.execute("SELECT * FROM User WHERE UserID = %s", (User_id_to_delete,))
            row = cursor.fetchone()

            # User is removed from usertable
            assert row is None, "User is stil in the UserTable"

            # devices are removed from Devicetable
            cursor.execute("SELECT * FROM Device WHERE UserID = %s", (User_id_to_delete,))
            row = cursor.fetchone()
            assert row is None, f"Devices belonging to user still in DeviceTable"

            # UserServices are removed from Devicetable
            cursor.execute("SELECT * FROM UserService WHERE UserID = %s", (User_id_to_delete,))
            row = cursor.fetchone()
            assert row is None, f"UserServices belonging to user still in UserServiceTable"

    def test_correct_get_user_from_device_id(self):
        user_ids = [1,2]
        device_ids = ["e1e1d2634929125249c7a4626573724b", "88039525d4f12b8fc4e0c4fc84fd4db4"]

        for user_id, device_id in zip(user_ids, device_ids):
            user = user_sql.get_user_from_device_id(device_id, self.db_conn_data)
            assert user is not None, f"User with id '{user_id}' not found"
            assert user["UserID"] == user_id, f"Returned user with id '{user['UserID']}' {user_id}!"

    def test_incorrect_get_user_from_device_id(self):
        device_ids = ["e1e1d2634929125250c7a4626573724b", "88039525a4f12b8fc4e0c4fc84fd4db4", "e1e1d2634929125249c7a4626573724c", "88039525d4f12b8fc4e0c4fc84fd4db3"]

        for device_id in device_ids:
            user = user_sql.get_user_from_device_id(device_id, self.db_conn_data)
            assert user is None, f"Invalid device_id gave returned user: '{user}'"
    
    def test_correct_verify_service_token(self):
        service_names = ["EmailService", "CloudStorage"]
        service_ids = [1,2]
        service_tokens = ["SERVICETOKENEMAIL","SERVICETOKENCLOUD"]

        for service_name, expected_service_id, service_token in zip(service_names, service_ids, service_tokens):
            is_valid_token, service_id = user_sql.verify_service_token(service_name, service_token, self.db_conn_data)
            assert is_valid_token, f"Token for service '{service_name}' is rated invalid!"
            assert service_id == expected_service_id, f"Returned wrong service_id, was f'{service_id}' and expected '{expected_service_id}'"

    def test_incorrect_verify_service_token(self):
        service_names = ["EmailService", "CloudStorage","CloudStorage", "EmailService"]
        service_tokens = ["SERVICETOKEN","TOKENCLOUD","SERVICETOKENEMAIL","SERVICETOKENCLOUD" ]

        for service_name, service_token in zip(service_names, service_tokens):
            is_valid_token, service_id = user_sql.verify_service_token(service_name, service_token, self.db_conn_data)
            assert not is_valid_token, f"Invalid Token '{service_token}' works for service '{service_name}'!"
            assert service_id is None, f"Service_id should be None for invalid serviceToken, instead returned f'{service_id}'"

    def test_correct_get_user_service_token_from_device(self):
        device_ids = ["e1e1d2634929125249c7a4626573724b", "e1e1d2634929125249c7a4626573724b", "88039525d4f12b8fc4e0c4fc84fd4db4"]
        service_names = ["EmailService", "CloudStorage", "EmailService"]
        user_service_tokens = ["d43249ae-4bbd-4b7b-b5d9-2271078233fa", "852691c1-51c0-434a-8900-c73fabad6518", "992f81a8-3bd1-4402-818a-7a4d824a85cd"]

        for device_id, service_name, user_service_token in zip(device_ids, service_names, user_service_tokens):
            user_service = user_sql.get_user_service_token_from_device(device_id, service_name, self.db_conn_data)
            assert user_service is not None, f"Did not find usertoken!"
            assert user_service["UserServiceToken"] == user_service_token, f"Wrong User-service Token '{user_service['UserServiceToken']}' should have been '{user_service_token}'"

    def test_incorrect_get_user_service_token_from_device(self):
        device_ids = ["e1e1d2634929125249c7a4626573724b", "85039525d4f12b8fc4e0c4fc84fd4db4"]
        service_names = ["CloudService", "EmailService"]
        error = ["Invalid serviceName", "Invalid DeviceID"]

        for device_id, service_name, error in zip(device_ids, service_names, error):
            user_service = user_sql.get_user_service_token_from_device(device_id, service_name, self.db_conn_data)
            assert user_service is None, f"Returned usertoken while testing with: {error}"

    def test_verify_user_TOTP_from_email(self):
        emails = ["admin@example.com", "alice@example.com"]
        totp_secrets = ["MEDBGLBEBFNBWVDNOIOSLTZMXDYVMOIL", "HBFRTISUR7HFH7DOW5OFEMSZELPUTQFG"]
        slide_window_sec = 10

        
        for email, totp_secret in zip(emails, totp_secrets):
            totp = pyotp.TOTP(totp_secret)
            time_0 = time.time()
            time_0 -= (time_0 % totp.interval)

            time_delay = 0
            while time_delay < totp.interval + slide_window_sec:
                testing_time = time_0# - time_delay
                totp_input = totp.at(testing_time)

                verify_result = user_sql.verify_user_TOTP_from_email(email, totp_input, slide_window_sec=slide_window_sec, verification_time=time_0+time_delay, db_conn_data=self.db_conn_data)
                assert verify_result, f"TOTP verification failed with email '{email}' and time delay '{time_delay}'"
                time_delay += 1

            # should fail after slide window accept 
            verify_result = user_sql.verify_user_TOTP_from_email(email, totp_input, slide_window_sec=slide_window_sec, verification_time=time_0+time_delay, db_conn_data=self.db_conn_data)
            assert not verify_result, f"TOTP verification worked after sliding window with time delay '{time_delay}'"

            # should fail for future values
            time_delay = -1
            verify_result = user_sql.verify_user_TOTP_from_email(email, totp_input, slide_window_sec=slide_window_sec, verification_time=time_0+time_delay, db_conn_data=self.db_conn_data)
            assert not verify_result, f"TOTP verification works for future codes tested with time delay '{time_delay}'"

    def test_invalid_flask_verify(self):
        # No Auth or cookies
        response = self.flask_app.get("/verify/service")
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert response.json == {'error': 'Requiring service Authorization', 'status code': 401}, f"this should fail: {response.json}"

        # wrong authorization Token 
        headers = {"Authorization": "Bearer WRONGTOKEN"}

        service_name = "EmailService" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert response.json == {'error': f"Could not verify service", 'status code': 401}, f"this should fail: {response.json}"

        # wrong authorization service_name
        headers = {"Authorization": "Bearer SERVICETOKENEMAIL"}

        service_name = "service" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert response.json == {'error': f"Could not verify service", 'status code': 401}, f"this should fail: {response.json}"

        # Missing device_id
        headers = {"Authorization": "Bearer SERVICETOKENEMAIL"}

        self.flask_app.set_cookie("hmac_secret", "8dd29d9c0cea896b8e0220c0cec6bec7")
        # self.flask_app.set_cookie("localhost", "hmac_secret", "8dd29d9c0cea896b8e0220c0cec6bec7")

        service_name = "EmailService" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert response.json == {'error': 'Invalid device_id or hmac_secret', 'status code': 401}, f"this should fail: {response.json}"

        self.flask_app.delete_cookie("hmac_secret")

        # Missing hmac_secret
        headers = {"Authorization": "Bearer SERVICETOKENEMAIL"}

        self.flask_app.set_cookie("device_id", "e1e1d2634929125249c7a4626573724b")

        service_name = "EmailService" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert response.json == {'error': 'Invalid device_id or hmac_secret', 'status code': 401}, f"this should fail: {response.json}"

        self.flask_app.delete_cookie("device_id")

        # invalid hmac_secret
        headers = {"Authorization": "Bearer SERVICETOKENEMAIL"}

        self.flask_app.set_cookie("device_id", "e1e1d2634929125249c7a4626573724b")
        self.flask_app.set_cookie("hmac_secret", "8dd29d9c0cea896b8e0220c0cec6bec8")

        service_name = "EmailService" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert response.json == {'error': "Could not verify Device", 'status code': 401}, f"this should fail: {response.json}"

        # invalid device_id
        headers = {"Authorization": "Bearer SERVICETOKENEMAIL"}

        self.flask_app.set_cookie("device_id", "e1e1d2634929125249c7a4626573724c")
        self.flask_app.set_cookie("hmac_secret", "8dd29d9c0cea896b8e0220c0cec6bec7")

        service_name = "EmailService" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert response.json == {'error': "Could not verify Device", 'status code': 401}, f"this should fail: {response.json}"

        # Overly long device_id should not crash and give quick error
        headers = {"Authorization": "Bearer SERVICETOKENCLOUD"}
        self.flask_app.set_cookie("device_id", "88039525d4f12b8fc4e0c4fc84fd4db488039525d4f12b8fc4e0c4fc84fd4db45")
        self.flask_app.set_cookie("hmac_secret", "8399403bd8b74d42c2820b6eab003d44")

        service_name = "CloudStorage" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert set(response.json.keys()) == set(["status code", "error"]), f"json has invalid keys - instead got: {response.json.keys()}"
        assert response.json['status code'] == 401, f"this http call should work with '200' instead got: {response.json['status code']}"
        assert response.json == {'error': 'Invalid device_id or hmac_secret', 'status code': 401}, f"this should fail: {response.json}"

        # Overly long hmac_secret should not crash and give quick error
        headers = {"Authorization": "Bearer SERVICETOKENCLOUD"}
        self.flask_app.set_cookie("device_id", "88039525d4f12b8fc4e0c4fc84fd4db4")
        self.flask_app.set_cookie("hmac_secret", "8399403bd8b74d42c2820b6eab003d448399403bd8b74d42c2820b6eab003d445")

        service_name = "CloudStorage" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert set(response.json.keys()) == set(["status code", "error"]), f"json has invalid keys - instead got: {response.json.keys()}"
        assert response.json['status code'] == 401, f"this http call should work with '200' instead got: {response.json['status code']}"
        assert response.json == {'error': 'Invalid device_id or hmac_secret', 'status code': 401}, f"this should fail: {response.json}"

        # User 2 SERVICE CLOUD 
        headers = {"Authorization": "Bearer SERVICETOKENCLOUD"}
        self.flask_app.set_cookie("device_id", "88039525d4f12b8fc4e0c4fc84fd4db4")
        self.flask_app.set_cookie("hmac_secret", "8399403bd8b74d42c2820b6eab003d44")

        service_name = "CloudStorage" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 401, f"this http call should fail with '401' instead got: {response.json}"
        assert set(response.json.keys()) == set(["status code", "error"]), f"json has invalid keys - instead got: {response.json.keys()}"
        assert response.json['status code'] == 401, f"this http call should work with '200' instead got: {response.json['status code']}"
        assert response.json == {'error': "User does not have sufficient permissions", 'status code': 401}, f"this should fail: {response.json}"

    def test_flask_verify_service_route(self):
        # User 1 SERVICE EMAIL 
        headers = {"Authorization": "Bearer SERVICETOKENEMAIL"}

        service_name = "EmailService" 

        self.flask_app.set_cookie("device_id", "e1e1d2634929125249c7a4626573724b")
        self.flask_app.set_cookie("hmac_secret", "8dd29d9c0cea896b8e0220c0cec6bec7")
        # self.flask_app.set_cookie("localhost", "device_id", "e1e1d2634929125249c7a4626573724b")
        # self.flask_app.set_cookie("localhost", "hmac_secret", "8dd29d9c0cea896b8e0220c0cec6bec7")
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 200, f"this http call should work with '200' instead got: {response.json}"
        assert set(response.json.keys()) == set(["status code", "status", "data"]), f"json has invalid keys - instead got: {response.json.keys()}"
        assert response.json['status code'] == 200, f"this http call should work with '200' instead got: {response.json['status code']}"
        assert response.json['status'] == 'ok', f"this http call should work with 'ok' instead got: {response.json['status']}"
        assert response.json['data'] == {'UserRole': 'admin', 'UserServiceToken': 'd43249ae-4bbd-4b7b-b5d9-2271078233fa'} , f"json data invalid - actually was: {response.json}"

        # User 1 SERVICE CLOUD 
        headers = {"Authorization": "Bearer SERVICETOKENCLOUD"}

        service_name = "CloudStorage" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 200, f"this http call should work with '200' instead got: {response.json}"
        assert set(response.json.keys()) == set(["status code", "status", "data"]), f"json has invalid keys - instead got: {response.json.keys()}"
        assert response.json['status code'] == 200, f"this http call should work with '200' instead got: {response.json['status code']}"
        assert response.json['status'] == 'ok', f"this http call should work with 'ok' instead got: {response.json['status']}"
        assert response.json['data'] == {'UserRole': 'admin', 'UserServiceToken': '852691c1-51c0-434a-8900-c73fabad6518'} , f"json data invalid - actually was: {response.json}"
        
        # New user credentials 
        self.flask_app.delete_cookie("device_id")
        self.flask_app.delete_cookie("hmac_secret")
        
        # User 2 SERVICE EMAIL
        headers = {"Authorization": "Bearer SERVICETOKENEMAIL"}
        self.flask_app.set_cookie("device_id", "88039525d4f12b8fc4e0c4fc84fd4db4")
        self.flask_app.set_cookie("hmac_secret", "8399403bd8b74d42c2820b6eab003d44")

        service_name = "EmailService" 
        response = self.flask_app.get(f"/verify/{service_name}", headers=headers)
        assert response.status_code == 200, f"this http call should work with '200' instead got: {response.json}"
        assert set(response.json.keys()) == set(["status code", "status", "data"]), f"json has invalid keys - instead got: {response.json.keys()}"
        assert response.json['status code'] == 200, f"this http call should work with '200' instead got: {response.json['status code']}"
        assert response.json['status'] == 'ok', f"this http call should work with 'ok' instead got: {response.json['status']}"
        assert response.json['data'] == {'UserRole': 'user', 'UserServiceToken': '992f81a8-3bd1-4402-818a-7a4d824a85cd'} , f"json data invalid - actually was: {response.json}"

if __name__ == "__main__":
    unittest.main()
# else:
    # print("DEBUG: Loaded tests:")
   #  suite = unittest.defaultTestLoader.loadTestsFromModule(user_test)
   #  print(suite)

    # unittest.TextTestRunner().run(suite)
    # unittest.main(argv=["first-arg-is-ignored"], exit=True)

