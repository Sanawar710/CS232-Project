import psycopg2 as pg  # 'psycopg2' is used to interact with the PostgreSQL database
import pandas as pd  # Pandas is a data manipulation and analysis library
from flask import Flask  # Flask is a high-level Python web framework
from flask import render_template # 'render_template' is used to render HTML files

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


# def authenticate(
#     name, password
# ):  # Authenticate function to verify username and password
#     '''
#     Args:
#         name (str): The username of the user.
#         password (str): The password of the user.
#     Returns:
#         bool: True if the username is "admin" and the password is "ABC", else False.
#     '''
#     return name == "admin" and password == "ABC"


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

    # Previous Tables to be Implemented till now
    createtable_script = '''CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
    profile_pic VARCHAR(255)
);'''
    cursor.execute(createtable_script)
    cursor.commit()
    
    createtable_script = '''
    CREATE TABLE Courses (
    course_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    credit_hours INT NOT NULL CHECK (credit_hours BETWEEN 1 AND 4),
    instructor_id INT,
    semester VARCHAR(20),
    FOREIGN KEY (instructor_id) REFERENCES Users(user_id)
);'''
    cursor.execute(createtable_script)
    cursor.commit()

    createtable_script = '''
    CREATE TABLE CoursePrerequisites (
    course_id INT,
    prerequisite_id INT,
    PRIMARY KEY (course_id, prerequisite_id),
    FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (prerequisite_id) REFERENCES Courses(course_id) ON DELETE CASCADE
);
    '''
    cursor.execute(createtable_script)
    cursor.commit()

    createtable_script = '''
    CREATE TABLE Registrations (
    registration_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    status VARCHAR(20) CHECK (status IN ('enrolled', 'completed', 'dropped')) DEFAULT 'enrolled',
    semester VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
);'''
    cursor.execute(createtable_script)
    cursor.commit()

    createtable_script = '''
 
    CREATE TABLE Results (
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
); '''
    cursor.execute(createtable_script)
    cursor.commit()


    createtable_script = '''
    CREATE TABLE Attendance (
    attendance_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(10) CHECK (status IN ('present', 'absent', 'late')) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
);'''
    cursor.execute(createtable_script)
    cursor.commit() 

    attendance_script = """
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        user_id INT,
        course_id INT,
        date DATE NOT NULL,
        status VARCHAR(10) CHECK (status IN ('absent', 'present', 'leave')) NOT NULL, 
        FOREIGN KEY (user_id) REFERENCES Users(id),
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    );
    """
    cursor.execute(attendance_script)
    conn.commit()

    message_script = """
    CREATE TABLE IF NOT EXISTS message(
       Message_id SERIAL PRIMARY KEY,
       FOREIGN KEY (sender_id) REFERENCES Users(id),
       FOREIGN KEY (receiver_id) REFERENCES Users(id),
       Message TEXT,
       Status VARCHAR(100),
       Time TIMESTAMP
       );"""
    cursor.execute(message_script)
    conn.commit()

    bug_script = """
    CREATE TABLE IF NOT EXISTS bug(
        bug_id SERIAL PRIMARY KEY,
        FOREIGN KEY (sender_id) REFERENCES Users(id),
        Description TEXT NOT NULL,
        status VARCHAR(10) CHECK (status IN ('open', 'in_progress', 'closed')) NOT NULL,
        Time TIMESTAMP
        );
   """
    cursor.execute(bug_script)
    conn.commit()

    rechcecking_script = """
    CREATE TABLE IF NOT EXISTS rechecking(
        recheck_id SERIAL PRIMARY KEY,
        FOREIGN KEY (sender_id) REFERENCES Users(id),
        FOREIGN KEY (course_id) REFERENCES Courses(id),
        reason TEXT NOT NULL,
        exam_type VARCHAR(10) CHECK (exam_type IN ('quiz', 'mid term', 'final')) NOT NULL,
        status VARCHAR(10) CHECK (status IN ('pending', 'approved', 'rejected')) NOT NULL,
        );
    """
    cursor.execute(rechcecking_script)
    conn.commit()

    academic_script = """
    CREATE TABLE IF NOT EXISTS academic_calendar(
        event_id SERIAL PRIMARY KEY,
        event_name VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        event_date DATE);
"""
    cursor.execute(academic_script)
    cursor.commit()

    feedback_script = """
    CREATE TABLE IF NOT EXISTS feedback(
       feedback_id SERIAL PRIMARY KEY,
       FOREIGN KEY (sender_id) REFERENCES Users(id),
       FOREIGN KEY (course_id) REFERENCES Courses(id),
       FOREIGN KEY (instructor_id) REFERENCES Users(id),
       rating INT CHECK (rating BETWEEN 1 AND 5),
       comments TEXT,
       time TIMESTAMP
       );"""

    cursor.execute(feedback_script)
    cursor.commit()


    # 1. Notify instructors of students with low performance
    low_performance_script = '''
    INSERT INTO message (sender_id, receiver_id, message)
    SELECT 
    R.user_id,
    C.instructor_id,
    'Student ' || U.name || ' has low quiz marks in ' || C.title
    FROM Results R
    JOIN Users U ON R.user_id = U.user_id
    JOIN Courses C ON R.course_id = C.course_id
    WHERE (R.quiz1 + R.quiz2) < 50;
    '''
    cursor.execute(low_performance_script)
    conn.commit()

    # 2. Recalculate total marks
    recalculate_script = '''
    UPDATE Results
    SET total_marks = quiz1 + quiz2 + midterm + final;
    '''
    cursor.execute(recalculate_script)
    conn.commit()

    # 3. View attendance of a specific student
    view_attendance_script = '''
    SELECT A.date, A.status, C.title
    FROM Attendance A
    JOIN Courses C ON A.course_id = C.course_id
    WHERE A.user_id = %s
    ORDER BY A.date;
    '''
    cursor.execute(view_attendance_script)
    conn.commit()

    # 4. View attendance of all students in a course
    view_attendance_course_script = '''
    SELECT U.name, A.date, A.status AS attendance_status
    FROM Attendance A
    JOIN Users U ON A.user_id = U.user_id
    JOIN Courses C ON A.course_id = C.course_id
    WHERE C.course_id = %s
    ORDER BY A.date;
    '''
    cursor.execute(view_attendance_course_script)
    conn.commit()

# 5. Get all students enrolled in a specific course
students_in_course_script = '''
SELECT U.user_id, U.name, U.email, R.status AS registration_status
FROM Users U
JOIN Registrations R ON U.user_id = R.user_id
JOIN Courses C ON R.course_id = C.course_id
WHERE C.course_id = %s;
'''
cursor.execute(students_in_course_script)
    conn.commit()

# 6. Calculate total and attended classes per student
attendance_summary_script = '''
SELECT A.user_id,
       A.course_id,
       COUNT(A.attendance_id) AS total_classes,
       COUNT(CASE WHEN A.status = 'present' THEN 1 END) AS attended_classes
FROM Attendance A
WHERE A.course_id = %s
GROUP BY A.user_id, A.course_id;
'''
ccursor.execute(attendance_summary_script)
    conn.commit()

# 7. Attendance percentage per student
attendance_percentage_script = '''
SELECT A.user_id,
       A.course_id,
       (COUNT(CASE WHEN A.status = 'present' THEN 1 END) * 1.0 / COUNT(A.attendance_id)) * 100 AS attendance_percentage
FROM Attendance A
WHERE A.course_id = %s
GROUP BY A.user_id, A.course_id;
'''
cursor.execute(attendance_percentage_script)
    conn.commit()

# 8. Insert attendance incentive (≥ 90%)
insert_incentive_script = '''
INSERT INTO Rewards (user_id, course_id, reward_type, reward_value)
SELECT A.user_id, A.course_id, 'attendance_incentive', 1
FROM Attendance A
WHERE A.course_id = %s
GROUP BY A.user_id, A.course_id
HAVING (COUNT(CASE WHEN A.status = 'present' THEN 1 END) * 1.0 / COUNT(A.attendance_id)) >= 0.9;
'''
cursor.execute(insert_incentive_script)
    conn.commit()

# 9. Add grading_type column to Courses
add_column_script = '''
ALTER TABLE Courses
ADD COLUMN grading_type VARCHAR(20)
CHECK (grading_type IN ('absolute', 'relative'));
'''
   cursor.execute(add_column_script)
   conn.commit()

   




    # Shouldn't we implement it with HTML and CSS instead of table?
    # dashboard_script = """
    # CREATE TABLE IF NOR EXIST dashboard(
    # theme VARCHAR(100),
    # layout TEXT);"""
    # cursor.execute(dasboard_script)
    # cursor.commit()

except Exception as e:
    print("Error:", e)
    print("Failed to connect to the database")

finally:
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()
