import mysql.connector
import os

class dbconnection():
    
    def __init__(self, connection_data_dict=None):
        self.db_connection_data_dict = {}

        if connection_data_dict and isinstance(connection_data_dict, dict):
            self.db_connection_data_dict = connection_data_dict
        else:
            self.db_connection_data_dict = {
                "host":os.environ.get("DB_HOST"),
                "user":os.environ.get("DB_USER"),
                "port":os.environ.get("DB_PORT"),
                "password":os.environ.get("DB_PASSWORD"),
                "database":os.environ.get("MYSQL_DATABASE")
            }

        self.conn = None
        self.cursor = None

    def __enter__(self, ):
        self.conn = mysql.connector.connect(**self.db_connection_data_dict)
        self.cursor = self.conn.cursor(dictionary=True)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            if exc_type is None:
                # No exception, commit the transaction
                self.conn.commit()
            else:
                # Exception occurred, rollback the transaction
                self.conn.rollback()
            self.conn.close()


