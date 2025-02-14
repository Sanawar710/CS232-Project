import psycopg2 as pg  # 'pscopg2' is used to interact with the PostgreSQL database
import flask
from flask import reuqest

def authenticate(
    name, password
):  # Authenticate function to verify username and password
    return name == "admin" and password == "ABC"


# Later to be modified, just a basic implementation of Admin's Class
class Admin:  # Admin Class to access admin panel
    operations = (
        "Add User",
        "Delete User",
        "Update User",
        "View User",
    )  # Operations that can be performed by the admin

    def __init__(self):
        print("Welcome to the Admin Panel")
        print("You can apply the following operations:")

        for i, operation in enumerate(self.operations, start=1):
            print(f"{i}. {operation}")

        operation_number = int(input("Enter the operation number: "))
        pass


# Database Connection Parameters
DB_Name = "Project"
DB_USER = "User-Name"
DB_Password = "Password"
DB_HOST = "localhost"  # The database is hosted locally
DB_Port = "5432"  # Default port that is used for PostgreSQL

try:
    conn = pg.connect(
        database=DB_Name, user=DB_USER, password=DB_Password, host=DB_HOST, port=DB_Port
    )
    cursor = conn.cursor()

    print("Connected to the database")

    # createTable_script = "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(50), age INT)" # Example SQL Query
    # cursor.execute(createTable_script)
    # cursor.commit()

    # insertValue_script = "INSERT VALUE INTO users (name, age) VALUES ('John', 25)"
    # cursor.execute(insertValue_script)
    # cursor.commit()
    
    # for i in cursor.fetchall() # Fetch all the rows from the table
    # print(f"Name: {i}, Age: {i}, ID: {i}") 
    
    # update_script = "UPDATE users SET age = 26 WHERE name = 'John'"
    # cursor.execute(update_script)
    # cursor.commit()
    
except Exception as e:
    print("Error: ", e)
    print("Failed to connect to the database")

finally:  # Will always be executed whether the try block is executed or not
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()