import psycopg2 as pg  # 'psycopg2' is used to interact with the PostgreSQL database
import pandas as pd  # Pandas is a data manipulation and analysis library
from flask import Flask  # Flask is a high-level Python web framework
from flask import render_template  # 'render_template' is used to render HTML files

df = pd.DataFrame()  # Global DataFrame to hold student data


def Absoulte_Grading():
    """
    This function applies absolute grading to the DataFrame based on fixed ranges.
    It assigns grades based on the specified ranges for each grade.
    """
    global df


try:
    df["Grade"] = pd.cut(
        df["Marks"],
        bins=[0, 50, 60, 70, 80, 100],
        labels=["F", "D", "C", "B", "A"],
        right=False,
    )
except KeyError:  # Marks column not found in the dataset
    pass
except Exception as e:  # Handle any other exceptions that may occur
    pass


def Relative_Grading():
    """
    This function applies relative grading to the DataFrame based on Z-scores.
    It calculates the mean and standard deviation of the "Marks" column and assigns grades based on Z-scores.
    """
    global df
    try:
        mean = df["Marks"].mean()
        std_dev = df["Marks"].std()

        # Assign grades based on Z-scores (Central Limit Theorem)
        def calculate_grade(marks):
            z_score = (marks - mean) / std_dev
            if z_score >= 1:
                return "A"
            elif 0.5 <= z_score < 1:
                return "B"
            elif -0.5 <= z_score < 0.5:
                return "C"
            elif -1 <= z_score < -0.5:
                return "D"
            else:
                return "F"

        df["Grade"] = df["Marks"].apply(calculate_grade)
    except KeyError:  # Marks column not found in the dataset
        pass
    except Exception as e:  # Handle any other exceptions that may occur
        pass


def authenticate(
    name, password
):  # Authenticate function to verify username and password
    """
    Args:
        name (str): The username of the user.
        password (str): The password of the user.
    Returns:
        bool: True if the username is "admin" and the password is "ABC", else False.
    """
    return name == "admin" and password == "ABC"


# # Later to be modified, just a basic implementation of Admin's Class
# class Admin:  # Admin Class to access admin panel
#     operations = (
#         "Add User",
#         "Delete User",
#         "Update User",
#         "View User",
#     )  # Operations that can be performed by the admin

#     def __init__(self):
#         """This is the function (similar to constructor in C++) that is called when an object of the class is created.
#         It will print the welcome message and the operations that can be performed by the admin (as of now).
#         """
#         print("Welcome to the Admin Panel")
#         print("You can apply the following operations:")

#         for i, operation in enumerate(self.operations, start=1):
#             print(f"{i}. {operation}")

#         # operation_number = int(input("Enter the operation number: "))
#         pass


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

    # User Table
    user_script = """CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
    profile_pic VARCHAR(255)
);"""
    cursor.execute(user_script)
    cursor.commit()

    student_script = """CREATE TABLE Students (
    program VARCHAR(50),
    semester INT
) INHERITS (Users);
"""
    cursor.execute(student_script)
    cursor.commit()

    instructor_script = """CREATE TABLE Instructors (
    department VARCHAR(100),
    designation VARCHAR(50)
) INHERITS (Users);"""
    cursor.execute(instructor_script)
    cursor.commit()

    admin_script = """CREATE TABLE Admins (
    role_description TEXT
) INHERITS (Users);
"""
    cursor.execute(admin_script)
    cursor.commit()

    # Courses Table
    courses_script = """CREATE TABLE Courses (
    course_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    credit_hours INT NOT NULL CHECK (credit_hours BETWEEN 1 AND 4),
    instructor_id INT,
    semester VARCHAR(20),
    FOREIGN KEY (instructor_id) REFERENCES Users(user_id)
);"""
    cursor.execute(courses_script)
    cursor.commit()

    # Course Prerequisites
    course_prerequisite_script = """CREATE TABLE CoursePrerequisites (
    course_id INT,
    prerequisite_id INT,
    PRIMARY KEY (course_id, prerequisite_id),
    FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (prerequisite_id) REFERENCES Courses(course_id) ON DELETE CASCADE
);"""
    cursor.execute(course_prerequisite_script)
    cursor.commit()

    # Registrations
    registration_script = """CREATE TABLE Registrations (
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
    cursor.commit()

    # Results
    result_script = """CREATE TABLE Results (
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
    cursor.commit()

    # Attendance
    attendance_script = """CREATE TABLE Attendance (
    attendance_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(10) CHECK (status IN ('present', 'absent', 'late')) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
);"""
    cursor.execute(attendance_script)
    cursor.commit()

    # Messages
    message_script = """CREATE TABLE IF NOT EXISTS message (
    Message_id SERIAL PRIMARY KEY,
    sender_id INT,
    receiver_id INT,
    Message TEXT,
    Status VARCHAR(100),
    Time TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES Users(user_id),
    FOREIGN KEY (receiver_id) REFERENCES Users(user_id)
);"""
    cursor.execute(message_script)
    cursor.commit()

    # Bugs
    bugs_script = """CREATE TABLE IF NOT EXISTS bug (
    bug_id SERIAL PRIMARY KEY,
    sender_id INT,
    Description TEXT NOT NULL,
    status VARCHAR(10) CHECK (status IN ('open', 'in_progress', 'closed')) NOT NULL,
    Time TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES Users(user_id)
);"""
    cursor.execute(bugs_script)
    cursor.commit()

    # Rechecking
    rechecking_script = """CREATE TABLE IF NOT EXISTS rechecking (
    recheck_id SERIAL PRIMARY KEY,
    sender_id INT,
    course_id INT,
    reason TEXT NOT NULL,
    exam_type VARCHAR(10) CHECK (exam_type IN ('quiz', 'mid term', 'final')) NOT NULL,
    status VARCHAR(10) CHECK (status IN ('pending', 'approved', 'rejected')) NOT NULL,
    FOREIGN KEY (sender_id) REFERENCES Users(user_id),
    FOREIGN KEY (course_id) REFERENCES Courses(course_id)
);"""
    cursor.execute(rechecking_script)
    cursor.commit()

    # Academic Calendar
    calendar_script = """CREATE TABLE IF NOT EXISTS academic_calendar (
    event_id SERIAL PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    event_date DATE
);"""
    cursor.execute(calendar_script)
    cursor.commit()

    # Feedback
    feedback_script = """CREATE TABLE IF NOT EXISTS feedback (
    feedback_id SERIAL PRIMARY KEY,
    sender_id INT,
    course_id INT,
    instructor_id INT,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comments TEXT,
    time TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES Users(user_id),
    FOREIGN KEY (course_id) REFERENCES Courses(course_id),
    FOREIGN KEY (instructor_id) REFERENCES Users(user_id)
);"""
    cursor.execute(feedback_script)
    cursor.commit()

    discussion_script = """CREATE TABLE DiscussionThreads (
    thread_id SERIAL PRIMARY KEY,
    mesage TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deleted', 'locked', 'archived')),
    FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE CASCADE
);
"""
    cursor.execute(discussion_script)
    cursor.commit()

except Exception as e:
    print("Error:", e)
    print("Failed to connect to the database")

finally:  # Will close the connection and cursor if they were created. It will be executed no matter what.
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()
