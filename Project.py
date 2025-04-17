import os
import psycopg2 as pg  # 'psycopg2' is used to interact with the PostgreSQL database
import pandas as pd  # Pandas is a data manipulation and analysis library
from flask import Flask, render_template, request, redirect, url_for, session  # Flask is a high-level Python web framework


df = pd.DataFrame()  # Global DataFrame to hold student data

def secret_key():
    """ Used to generate a secret key that will be used while hosting the application on the web with security

    Returns:
        Secret key in hexadecimal format
    """
    secret_bytes = os.urandom(24)  # Generates 24 random bytes
    secret_key_bytes = secret_bytes.hex() # Converts the variable 'secret_bytes' into hexadecimal format
    return secret_key_bytes

app = Flask(__name__)
app.secret_key = secret_key()

# Database Connection Parameters
DB_Name = "LMS"
DB_USER = "User-Name"
DB_Password = "Password"
DB_HOST = "localhost"
DB_Port = "5432"

def authenticate(name, password):
    """
    Args:
        name (str): The username of the user.
        password (str): The password of the user.
    Returns:
        bool: True if the username is "admin" and the password is "ABC", else False.
    """
    return name == "admin" and password == "ABC"


def Absolute_Grading(cursor):
    """
    Applies absolute grading to students' marks and updates the 'Grade' column in the 'Results' table.
    Grading is based on fixed marks ranges.
    """
    try:
        update_query = """UPDATE Results
        SET Grade = CASE
            WHEN total_marks >= 80 THEN 'A'
            WHEN total_marks >= 70 THEN 'B'
            WHEN total_marks >= 60 THEN 'C'
            WHEN total_marks >= 50 THEN 'D'
            ELSE 'F'
        END;
        """
        cursor.connection.commit(update_query)
        print("Absolute grading applied successfully.")
    except Exception as e:
        print("Error in Absolute Grading:", e)
        conn.rollback()  # Discards unwanted changes


def relative_grading(cursor):
    """This function is used to caluclate the relative grade of the student based on the Z-Score."""
    try:
        # Calculate the mean and standard deviation for relative grading
        cursor.execute("SELECT AVG(Marks), STDDEV(Marks) FROM Results;")
        mean, stddev = cursor.fetchone()

        # Using the CASE expression to categorize grades based on mean and stddev
        cursor.execute(
            """UPDATE Results
            SET grade = CASE
                WHEN Marks >= %s + 1 * %s THEN 'A'
                WHEN Marks >= %s + 0.5 * %s THEN 'B'
                WHEN Marks >= %s - 0.5 * %s THEN 'C'
                WHEN Marks >= %s - 1 * %s THEN 'D'
                ELSE 'F'
            END
        """,
            (mean, stddev, mean, stddev, mean, stddev, mean, stddev),
        )

        # Commit the changes to the database
        cursor.connection.commit()

    except Exception as e:
        print(f"Error: {e}")


def insert_data(cursor, table, columns, values):
    """
    Inserts data into a specified table.

    Args:
        cursor (psycopg2.cursor): The cursor object to execute queries.
        table (str): Name of the table.
        columns (list): List of column names.
        values (list): List of values corresponding to the columns.

    Returns:
        None
    """
    try:
        # Constructing the INSERT SQL query
        # .join(columns) joins the column names with commas (e.g. "col1, col2")
        # %s is a placeholder for values to be inserted (the parameters will replace the placeholders)
        # ['%s'] * len(values) creates a new list where ['%s'] is repeated len(values) times.
        # This is used to match the number of columns in the VALUES clause
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(values))})"

        # Executing the query with provided values
        cursor.execute(query, values)
        print(f"Data inserted successfully into {table}")

    except Exception as e:
        print("Error:", e)
        print(f"Failed to insert data into {table}")


def update_table_value(
    cursor, conn, table, column_to_update, new_value, condition_column, condition_value
):
    """Used to update the value of a specific column in a table based on a condition.

    Args:
        cursor: psycopg2 cursor object
        conn: psycopg2 connection object
        table: Name of the table
        column_to_update: Name of the column to be updated
        new_value: The value to be inserted instead of the old one
        condition_column: The column on which the condition is to be applied
        condition_value: Value to be matched for the condition
    """

    try:
        query = f"""UPDATE {table}
        SET {column_to_update} = %s
        WHERE {condition_column} = %s;
        """
        cursor.execute(query, (new_value, condition_value))
        conn.commit()
        print(
            f"Updated {column_to_update} to {new_value} in {table} where {condition_column} = {condition_value}"
        )
    except Exception as e:
        conn.rollback()
        print("Can not update the value:", e)


# Initialize connection and cursor
conn = None
cursor = None

try:
    conn = pg.connect(
        database=DB_Name,
        user=DB_USER,
        password=DB_Password,
        host=DB_HOST,
        port=DB_Port,
    )
    
    cursor = conn.cursor()
    print("Connected to the database")

    user_script = """CREATE TABLE Users (
        user_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'instructor', 'admin'))
    );"""
    cursor.execute(user_script)
    conn.commit()

    student_script = """CREATE TABLE IF NOT EXISTS Students (
        program VARCHAR(50),
        semester INT
    ) INHERITS (Users);"""
    cursor.execute(student_script)
    conn.commit()

    instructor_script = """CREATE TABLE IF NOT EXISTS Instructors (
        department VARCHAR(100),
        designation VARCHAR(50)
    ) INHERITS (Users);"""
    cursor.execute(instructor_script)
    conn.commit()

    admin_script = """CREATE TABLE IF NOT EXISTS Admins (
        role_description TEXT
    ) INHERITS (Users);"""
    cursor.execute(admin_script)
    conn.commit()

    courses_script = """CREATE TABLE IF NOT EXISTS Courses (
        course_id SERIAL PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        credit_hours INT NOT NULL CHECK (credit_hours BETWEEN 1 AND 4),
        instructor_id INT,
        semester VARCHAR(20),
        FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );"""
    cursor.execute(courses_script)
    conn.commit()

    course_prerequisite_script = """CREATE TABLE IF NOT EXISTS CoursePrerequisites (
        course_id INT,
        prerequisite_id INT,
        PRIMARY KEY (course_id, prerequisite_id),
        FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
        FOREIGN KEY (prerequisite_id) REFERENCES Courses(course_id) ON DELETE CASCADE
    );"""
    cursor.execute(course_prerequisite_script)
    conn.commit()

    registration_script = """CREATE TABLE IF NOT EXISTS Registrations (
        registration_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        course_id INT NOT NULL,
        status VARCHAR(20) DEFAULT 'enrolled',
        semester VARCHAR(20),
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
        CHECK (
            (semester = '1' AND status = 'enrolled') OR
            (semester <> '1' AND status IN ('enrolled', 'completed', 'dropped'))
        )
    );"""
    cursor.execute(registration_script)
    conn.commit()

    result_script = """CREATE TABLE IF NOT EXISTS Results (
        result_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        course_id INT NOT NULL,
        quiz1 FLOAT DEFAULT 0,
        quiz2 FLOAT DEFAULT 0,
        midterm FLOAT DEFAULT 0,
        final FLOAT DEFAULT 0,
        total_marks FLOAT DEFAULT 0,
        grade VARCHAR(2),
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
    );"""
    cursor.execute(result_script)
    conn.commit()

    attendance_script = """CREATE TABLE IF NOT EXISTS Attendance (
        attendance_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        course_id INT NOT NULL,
        date DATE NOT NULL,
        status VARCHAR(10) CHECK (status IN ('present', 'absent', 'late')) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
    );"""
    cursor.execute(attendance_script)
    conn.commit()

    message_script = """CREATE TABLE IF NOT EXISTS message (
        Message_id SERIAL PRIMARY KEY,
        sender_id INT,
        receiver_id INT,
        Message TEXT,
        Status VARCHAR(100),
        Time TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (receiver_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );"""
    cursor.execute(message_script)
    conn.commit()

    bugs_script = """CREATE TABLE IF NOT EXISTS bug (
        bug_id SERIAL PRIMARY KEY,
        sender_id INT,
        Description TEXT NOT NULL,
        status VARCHAR(10) CHECK (status IN ('open', 'in_progress', 'closed')) NOT NULL,
        Time TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );"""
    cursor.execute(bugs_script)
    conn.commit()

    rechecking_script = """CREATE TABLE IF NOT EXISTS rechecking (
        recheck_id SERIAL PRIMARY KEY,
        sender_id INT,
        course_id INT,
        reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        exam_type VARCHAR(10) CHECK (exam_type IN ('quiz', 'mid term', 'final')) NOT NULL,
        status VARCHAR(10) CHECK (status IN ('pending', 'approved', 'rejected')) NOT NULL,
        FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
    );"""
    cursor.execute(rechecking_script)
    conn.commit()

    calendar_script = """CREATE TABLE IF NOT EXISTS academic_calendar (
        event_id SERIAL PRIMARY KEY,
        event_name VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        event_date DATE
    );"""
    cursor.execute(calendar_script)
    conn.commit()

    feedback_script = """CREATE TABLE IF NOT EXISTS feedback (
        feedback_id SERIAL PRIMARY KEY,
        sender_id INT,
        course_id INT,
        instructor_id INT,
        rating INT CHECK (rating BETWEEN 1 AND 5),
        comments TEXT,
        time TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
        FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );"""
    cursor.execute(feedback_script)
    conn.commit()

    # We created a recheck_appointments table and added a created_at column to track recheck request times. The status of rechecks is automatically updated based on time.
    recheck_appointments_script = """CREATE TABLE IF NOT EXISTS recheck_appointments (
    appointment_id SERIAL PRIMARY KEY,
    recheck_id INT UNIQUE,
    appointment_time TIMESTAMP NOT NULL,
    remarks TEXT,
    FOREIGN KEY (recheck_id) REFERENCES rechecking(recheck_id) ON DELETE CASCADE
    );"""
    cursor.execute(recheck_appointments_script)
    conn.commit()

    update_rechecking_status_script = """ UPDATE rechecking
    SET status = CASE 
                WHEN status = 'pending' AND CURRENT_TIMESTAMP - created_at > INTERVAL '10 days' THEN 'rejected'
                WHEN status = 'pending' AND CURRENT_TIMESTAMP - created_at > INTERVAL '7 days' THEN 'approved'
                ELSE status
             END
    WHERE status = 'pending';
    """
    cursor.execute(update_rechecking_status_script)
    conn.commit()

    discussion_script = """CREATE TABLE DiscussionThreads (
        thread_id SERIAL PRIMARY KEY,
        mesage TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deleted', 'locked', 'archived')),
        FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
        FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );"""
    cursor.execute(discussion_script)
    conn.commit()

except Exception as e:
    print("Error:", e)
    print("Failed to connect to the database")

finally:
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()
