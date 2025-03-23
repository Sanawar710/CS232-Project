import psycopg2 as pg  # 'psycopg2' is used to interact with the PostgreSQL database
import django  # Django is a high-level Python web framework 

def authenticate(
    name, password
):  # Authenticate function to verify username and password
    '''
    Args:
        name (str): The username of the user.
        password (str): The password of the user.
    Returns:
        bool: True if the username is "admin" and the password is "ABC", else False.
    '''
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
        """This is the function (similar to constructor in C++) that is called when an object of the class is created.
        It will print the welcome message and the operations that can be performed by the admin (as of now).
        """
        print("Welcome to the Admin Panel")
        print("You can apply the following operations:")

        for i, operation in enumerate(self.operations, start=1):
            print(f"{i}. {operation}")

        # operation_number = int(input("Enter the operation number: "))
        pass


# Database Connection Parameters
DB_Name = "Project"
DB_USER = "User-Name"
DB_Password = "Password"
DB_HOST = "localhost"  # The database is hosted locally
DB_Port = "5432"  # Default port that is used for PostgreSQL

# Initialize connection and cursor
conn = None
cursor = None

try:
    conn = pg.connect(
        database=DB_Name, user=DB_USER, password=DB_Password, host=DB_HOST, port=DB_Port
    )
    cursor = conn.cursor()

    print("Connected to the database")

    # createTable_script = "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(50), age INT)" # Example SQL Query
    # cursor.execute(createTable_script)
    # conn.commit()

    # insertValue_script = "INSERT INTO users (name, age) VALUES ('John', 25)"
    # cursor.execute(insertValue_script)
    # conn.commit()

    # cursor.execute("SELECT * FROM users")  # Fetch all rows from the table
    # for row in cursor.fetchall():
    #     print(f"Name: {row[1]}, Age: {row[2]}, ID: {row[0]}")

    # update_script = "UPDATE users SET age = 26 WHERE name = 'John'"
    # cursor.execute(update_script)
    # conn.commit()

except Exception as e:
    print("Error:", e)
    print("Failed to connect to the database")

finally:  # This will always be executed
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()