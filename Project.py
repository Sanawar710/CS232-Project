import tkinter as tk  # 'tkinter' is used for creating GUI applications
import psycopg2 as pg  # 'psycopg2' is used to interact with the PostgreSQL database
from psycopg2 import sql # 'sql' is used for SQL query construction and preventing SQL injection
import pandas as pd  # 'pandas' is a data manipulation and analysis library
import matplotlib.pyplot as plt  # 'matplotlib' is used for plotting graphs
import numpy as np  # 'numpy' is used for numerical operations

df = pd.DataFrame()  # Global DataFrame to hold student data

# Database Connection Parameters
DB_Name = "LMS"
DB_USER = "User-Name"
DB_Password = "admin"
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


def absolute_grading(cursor, conn):
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
        cursor.execute(update_query)
        conn.commit()

        print("Absolute grading applied successfully.")
    except Exception as e:
        print("Error in Absolute Grading:", e)
        conn.rollback()  # Discards unwanted changes


def relative_grading(cursor):
    """This function is used to caluclate the relative grade of the student based on the Z-Score."""
    try:
        # Calculate the mean and standard deviation for relative grading
        cursor.execute("SELECT AVG(total_marks), STDDEV(total_marks) FROM Results;")
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
        conn.commit()

    except Exception as e:
        print(f"Error: {e}")


def plot_percentage_distribution(
    cursor, conn, table_name="Results", column_name="total_marks"
):
    try:
        query = f"SELECT {column_name} FROM {table_name};"
        cursor.execute(query)
        rows = cursor.fetchall()
        percentages = [row[0] for row in rows]

        if not percentages:
            print("No data found in the table.")
            return

        data = np.array(percentages)
        mean = np.mean(data)
        std_dev = np.std(data)

        # Histogram
        count, bins, ignored = plt.hist(
            data, bins=20, density=True, alpha=0.6, color="skyblue", edgecolor="black"
        )

        # Normal curve
        x = np.linspace(
            min(data), max(data), 100
        )  # Create an array of 100 evenly spaced values between the minimum and maximum of the data
        y = (1 / (std_dev * np.sqrt(2 * np.pi))) * np.exp(
            -0.5 * ((x - mean) / std_dev) ** 2
        )
        plt.plot(x, y, color="red", linewidth=2)

        # Labels
        plt.title("Normal Distribution of Total Percentages")
        plt.xlabel("Total Percentage")
        plt.ylabel("Density")
        plt.grid(True)
        plt.show()

    except Exception as e:
        print("Error:", e)
        conn.rollback()  # Discards unwanted changes


def insert_course_prerequisite(course_id, prereq_id, cursor, conn):
    script = """INSERT INTO CoursePrerequisites (course_id, prerequisite_id) VALUES (%s, %s);"""
    cursor.execute(script, (course_id, prereq_id))
    conn.commit()


def insert_user(name, email, password, role, profile_pic, cursor, conn):
    script = """INSERT INTO Users(name, email, password, role, profile_pic) VALUES (%s, %s, %s, %s, %s);"""
    cursor.execute(script, (name, email, password, role, profile_pic))
    conn.commit()


def insert_course(title, credit_hours, instructor_id, semester, cursor, conn):
    script = """INSERT INTO Courses (title, credit_hours, instructor_id, semester) VALUES (%s, %s, %s, %s);"""
    cursor.execute(script, (title, credit_hours, instructor_id, semester))
    conn.commit()


def insert_registration(user_id, course_id, status, semester, cursor, conn):
    script = """INSERT INTO Registrations(user_id, course_id, status, semester) VALUES (%s, %s, %s, %s);"""
    cursor.execute(script, (user_id, course_id, status, semester))
    conn.commit()


def insert_result(
    user_id, course_id, quiz1, quiz2, midterm, final, total_marks, grade, cursor, conn
):
    script = """INSERT INTO Results (user_id, course_id, quiz1, quiz2, midterm, final, total_marks, grade) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""
    cursor.execute(
        script, (user_id, course_id, quiz1, quiz2, midterm, final, total_marks, grade)
    )
    conn.commit()


def insert_attendance(user_id, course_id, date, status, cursor, conn):
    script = """INSERT INTO Attendance (user_id, course_id, date, status) VALUES (%s, %s, %s, %s);"""
    cursor.execute(script, (user_id, course_id, date, status))
    conn.commit()


def insert_message(sender_id, receiver_id, message, status, time, cursor, conn):
    script = """INSERT INTO message(sender_id, receiver_id, message, status, time) VALUES (%s, %s, %s, %s, %s);"""
    cursor.execute(script, (sender_id, receiver_id, message, status, time))
    conn.commit()


def insert_bug(sender_id, description, status, time, cursor, conn):
    script = """INSERT INTO bug(sender_id, description, status, time) VALUES (%s, %s, %s, %s);"""
    cursor.execute(script, (sender_id, description, status, time))
    conn.commit()


def insert_rechecking(sender_id, course_id, reason, exam_type, status, cursor, conn):
    script = """INSERT INTO rechecking(sender_id, course_id, reason, exam_type, status) 
                VALUES (%s, %s, %s, %s, %s);"""
    cursor.execute(script, (sender_id, course_id, reason, exam_type, status))
    conn.commit()


def insert_calendar_event(event_name, description, event_date, cursor, conn):
    script = """INSERT INTO academic_calendar(event_name, description, event_date) VALUES (%s, %s, %s);"""
    cursor.execute(script, (event_name, description, event_date))
    conn.commit()


def insert_feedback(
    sender_id, course_id, instructor_id, rating, comments, time, cursor, conn
):
    script = """INSERT INTO feedback(sender_id, course_id, instructor_id, rating, comments, time)
                VALUES (%s, %s, %s, %s, %s, %s);"""
    cursor.execute(
        script, (sender_id, course_id, instructor_id, rating, comments, time)
    )
    conn.commit()


def insert_recheck_appointment(recheck_id, appointment_time, remarks, cursor, conn):
    script = """INSERT INTO recheck_appointments(recheck_id, appointment_time, remarks) VALUES (%s, %s, %s);"""
    cursor.execute(script, (recheck_id, appointment_time, remarks))
    conn.commit()


def update_rechecking_auto_status(cursor, conn):
    script = """UPDATE rechecking
        SET status = CASE 
            WHEN status = 'pending' AND CURRENT_TIMESTAMP - created_at > INTERVAL '10 days' THEN 'rejected'
            WHEN status = 'pending' AND CURRENT_TIMESTAMP - created_at > INTERVAL '7 days' THEN 'approved'
            ELSE status
        END
        WHERE status = 'pending';
    """
    cursor.execute(script)
    conn.commit()


def insert_discussion_thread(
    course_id, instructor_id, message, status, created_at, cursor, conn
):
    script = """INSERT INTO DiscussionThreads(course_id, instructor_id, message, status, created_at)
                VALUES (%s, %s, %s, %s, %s);"""
    cursor.execute(script, (course_id, instructor_id, message, status, created_at))
    conn.commit()


def updateVal_message(
    cursor, conn, Message_id, sender_id, receiver_id, Message, Status, Time
):
    script = """UPDATE message SET sender_id = %s, receiver_id = %s, Message = %s, Status = %s, Time = %s WHERE Message_id = %s;"""
    cursor.execute(script, (sender_id, receiver_id, Message, Status, Time, Message_id))
    conn.commit()


def updateVal_bug(cursor, conn, bug_id, sender_id, Description, status, Time):
    script = """UPDATE bug SET sender_id = %s, Description = %s, status = %s, Time = %s WHERE bug_id = %s;"""
    cursor.execute(script, (sender_id, Description, status, Time, bug_id))
    conn.commit()


def updateVal_rechecking(
    cursor,
    conn,
    recheck_id,
    sender_id,
    course_id,
    reason,
    created_at,
    exam_type,
    status,
):
    script = """
    UPDATE rechecking
    SET sender_id = %s,
        course_id = %s,
        reason = %s,
        created_at = %s,
        exam_type = %s,
        status = %s
    WHERE recheck_id = %s;
    """
    cursor.execute(
        script,
        (sender_id, course_id, reason, created_at, exam_type, status, recheck_id),
    )
    conn.commit()


def updateVal_feedback(
    cursor,
    conn,
    feedback_id,
    sender_id,
    course_id,
    instructor_id,
    rating,
    comments,
    time,
):
    script = """UPDATE feedback SET sender_id = %s, course_id = %s, instructor_id = %s, rating = %s, comments = %s, time = %s WHERE feedback_id = %s;"""
    cursor.execute(
        script,
        (sender_id, course_id, instructor_id, rating, comments, time, feedback_id),
    )
    conn.commit()


def updateVal_academic_calendar(
    cursor, conn, event_id, event_name, description, event_date
):
    script = """UPDATE academic_calendar SET event_name = %s, description = %s, event_date = %s WHERE event_id = %s;"""
    cursor.execute(script, (event_name, description, event_date, event_id))
    conn.commit()


def deleteVal_message(cursor, conn, Message_id):
    script = """DELETE FROM message WHERE Message_id = %s;"""
    cursor.execute(script, (Message_id,))
    conn.commit()


def deleteVal_bug(cursor, conn, bug_id):
    script = """DELETE FROM bug WHERE bug_id = %s;"""
    cursor.execute(script, (bug_id,))
    conn.commit()


def deleteVal_rechecking(cursor, conn, recheck_id):
    script = """DELETE FROM rechecking WHERE recheck_id = %s;"""
    cursor.execute(script, (recheck_id,))
    conn.commit()


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

    # We created a recheck_appointments table and added a created_at column to track recheck request times. The status of rechecks is automatically updated based on time.
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

    class Menu:
        def __init__(self):
            self.user = None
            self.admin = None

        def display_menu(self):
            print("Welcome to the Learning Management System")
            print("1. Login as User")
            print("2. Login as Admin")
            print("3. Exit")

        def login(self):
            while True:
                self.display_menu()
                choice = input("Choose an option: ")

                if choice == "1":
                    # self.user = User()
                    self.user.login()
                    break
                elif choice == "2":
                    # self.admin = Admin()
                    self.admin.login()
                    break
                elif choice == "3":
                    print("Exiting... Goodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")

    class User:
        def __init__(self, conn):
            self.conn = conn
            self.cursor = conn.cursor()
            self.user_id = None
            self.name = ""
            self.email = ""
            self.password = ""
            self.role = ""
            self.logged_in = False

        def login(self):
            email = input("Enter your email: ")
            password = input("Enter your password: ")

            query = sql.SQL(
                "SELECT user_id, name, email, password, role FROM Users WHERE email = %s AND password = %s"
            )
            self.cursor.execute(query, (email, password))

            user = self.cursor.fetchone()

            if user:
                self.user_id, self.name, self.email, self.password, self.role = user
                self.logged_in = True
                print(f"Welcome, {self.name} ({self.role})!")
                self.user_menu()
            else:
                print("Invalid credentials. Please try again.")

        def user_menu(self):
            while self.logged_in:
                print("\nUser Menu:")
                if self.role == "student":
                    print("1. View Courses")
                    print("2. View Grades")
                    print("3. View Attendance")
                elif self.role == "instructor":
                    print("1. View Courses")
                    print("2. Add Grade")
                    print("3. View Student Attendance")
                elif self.role == "admin":
                    print("1. Add User")
                    print("2. View All Users")
                    print("3. Manage System Settings")

                print("4. Logout")
                choice = input("Choose an option: ")

                if choice == "1":
                    self.view_courses()
                elif choice == "2":
                    self.view_grades()
                elif choice == "3":
                    self.view_attendance()
                elif choice == "4":
                    print("Logging out...")
                    self.logged_in = False
                    break
                else:
                    print("Invalid choice. Please try again.")

        def view_courses(self):
            if self.role == "student":
                print("Fetching courses for student...")
                # Add logic to fetch and display courses for the student from database
            elif self.role == "instructor":
                print("Fetching courses taught by instructor...")
                # Add logic to fetch and display courses taught by the instructor from database
            else:
                print("You don't have permission to view courses.")

        def view_grades(self):
            if self.role == "student":
                print("Fetching your grades...")
                # Add logic to fetch and display the student's grades from database
            elif self.role == "instructor":
                print("Fetching grades for your courses...")
                # Add logic to fetch and display the grades for the instructor's courses
            else:
                print("You don't have permission to view grades.")

        def view_attendance(self):
            if self.role == "student":
                print("Fetching your attendance...")
                # Add logic to fetch and display the student's attendance from database
            elif self.role == "instructor":
                print("Fetching attendance for your students...")
                # Add logic to fetch and display attendance for the instructor's students
            else:
                print("You don't have permission to view attendance.")

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
