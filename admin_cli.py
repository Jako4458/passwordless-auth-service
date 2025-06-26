from dotenv import load_dotenv

if not load_dotenv(".env.admin_cli"):
    print("ERROR LOADING TESTING ENVIRONMENT!")

from utils.user_sql import *

db_conn_data = {
    "host":os.environ.get("DB_HOST"),
    "user":os.environ.get("DB_USER"),
    "port":int(os.environ.get("DB_PORT")),
    "password":os.environ.get("DB_PASSWORD"),
    "database":os.environ.get("MYSQL_DATABASE")
}

print(db_conn_data)

## db_conn_data = {
    ## "user": "testuser",
    ## "password": "testpass",
    ## "database": "testdb",
    ## "host": "localhost",
    ## "port" : 3307
## }

def list_all_items_by_input():
    action = ""
    while (not action.isdigit()) or (int(action) < 1 and int(action) > 4):
        print("Show all:")
        
        print("1) Users")
        print("2) Services")
        print("3) Devices")
        print("4) UserServices")
        print()
        action = input("What do you want to show: ") 

    action = int(action)


    if action == 1:
        item_list = get_all_users_as_list(db_conn_data) 
        print("Users:")
    elif action == 2:
        item_list = get_all_services_as_list(db_conn_data) 
        print("Services:")
    elif action == 3:
        item_list = get_all_devices_as_list(db_conn_data) 
        print("Devices:")
    elif action == 4:
        item_list = get_all_user_services_as_list(db_conn_data) 
        print("UserServices:")

    for item in item_list:
        print(item)

def update_user():
    action = ""
    while (not action.isdigit()) or (int(action) < 1 and int(action) > 2):
        print("Show all:")
        
        print("1) Add User")
        print("2) Delete User")
        print()
        action = input("What do you want to show: ") 

    action = int(action)

    if action == 1:
        totp_secret, _ = add_user_from_input(db_conn_data)
        print(f"totp secret: {totp_secret}")
    elif action == 2:
        user_id = input("Enter id of user to delete: ")
        delete_user_from_id(user_id, db_conn_data)

def update_service():
    action = ""
    while (not action.isdigit()) or (int(action) < 1 and int(action) > 2):
        print("Show all:")
        
        print("1) Add Service")
        print("2) Delete Service")
        print()
        action = input("What do you want to show: ") 

    action = int(action)

    if action == 1:
        service_name = input("Enter name of service: ")
        service = add_service(service_name, db_conn_data)
        print(f"Service token: {service['token']}")
    if action == 2:
        service_id = input("Enter id of service to delete: ")
        delete_service_from_id(service_id, db_conn_data)

def update_device():
    action = ""
    while (not action.isdigit()) or (int(action) < 2 and int(action) > 2):
        print("Show all:")
        

        print("Devices cant be added from cli but only browser!")
        print("2) Delete Device")
        print()
        action = input("What do you want to show: ") 

    action = int(action)

    if action == 2:
        device_id = input("Enter id of device to delete: ")
        delete_device_from_id(device_id, db_conn_data)


def update_user_service():
    action = ""
    while (not action.isdigit()) or (int(action) < 1 and int(action) > 2):
        print("Show all:")
        
        print("1) Add UserService")
        print("2) Delete UserService")
        print()
        action = input("What do you want to show: ") 

    action = int(action)

    if action == 1:
        user_id = ("Enter UserID: ")
        service_id = ("Enter ServiceID: ")
        user_service = add_user_service(user_id, service_id, db_conn_data)
    elif action == 2:
        user_id = ("Enter UserID to delete UserService from: ")
        service_id = ("Enter ServiceID to delete UserService from: ")
        delete_user_service_from_user_id_and_service_id(user_id, service_id, db_conn_data)

if __name__ == "__main__":
    action = ""

    actions = {
            ("1","List table"): list_all_items_by_input,
            ("2","Manage Users"): update_user,
            ("3","Manage Services"): update_service,
            ("4","Manage Devices"): update_device,
            ("5","Manage UserServices"): update_user_service,
            }
    while action != "q":
        print("Possible actions:")
        
        for index, func in actions.items():
            i, text = index
            print(f"{i}) {text}")

        print()
        print("q) quit")
        print()
        action = input("What do you want to do: ") 

        if action == "q":
            exit()
        elif action.isdigit():
            list(actions.values())[int(action)-1]()

        print()
