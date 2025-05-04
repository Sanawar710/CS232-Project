import tkinter as tk  # 'tkinter' is a standard GUI toolkit in Python.
from tkinter import ttk, messagebox  # 'ttk' is a themed widget set for tkinter.
import psycopg2 as pg  # 'psycopg2' is used to connect to PostgreSQL databases with Python.
import pandas as pd  # 'pandas' is a data manipulation and analysis library.
import numpy as np  # 'numpy' is a library for numerical computations in Python.
import matplotlib.pyplot as plt  # 'matplotlib' is a plotting library for Python.
import datetime  # 'datetime' is a module for manipulating dates and times.

df = pd.DataFrame()

# Database Connection Parameters
DB_Name = "LMS"
DB_USER = "postgres"
DB_Password = "admin"
DB_HOST = "localhost"
DB_Port = "5432"


def connect_db():
    """Connect to the PostgreSQL database and return the connection and cursor."""
    try:
        conn = pg.connect(
            database=DB_Name,
            user=DB_USER,
            password=DB_Password,
            host=DB_HOST,
            port=DB_Port,
        )
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        messagebox.showerror(
            "Database Error", f"Failed to connect to the database: {e}"
        )
        return None, None


def close_db(conn, cursor):
    """Close the database connection and cursor.

    Args:
        conn : The database connection object.
        cursor : The database cursor object.
    """
    if cursor:
        cursor.close()
    if conn:
        conn.close()


def execute_query(conn, cursor, query, params=None, fetch=False):
    """Execute a SQL query with optional parameters.

    This function handles both SELECT and non-SELECT queries. If 'fetch' is True, it fetches the results.

    Args:
        conn : The database connection object.
        cursor : The database cursor object.
        query (_type_): The SQL query to execute.
        params (_type_, optional): The parameters to pass to the query. Defaults to None.
        fetch (bool, optional): Whether to fetch results. Defaults to False.
    Returns:
        _type_: The result of the query if 'fetch' is True, otherwise None.
    """
    try:
        cursor.execute(query, params)
        conn.commit()
        if fetch:
            return cursor.fetchall()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Query Error", f"Error executing query: {e}")
        return False


def absolute_grading(conn, cursor, course_id):
    query = """ UPDATE Results
    SET Grade = CASE
        WHEN total_marks >= 80 THEN 'A'
        WHEN total_marks >= 70 THEN 'B'
        WHEN total_marks >= 60 THEN 'C'
        WHEN total_marks >= 50 THEN 'D'
        ELSE 'F'
    END
    WHERE course_id = %s
    """
    if execute_query(conn, cursor, query, (course_id,)):
        messagebox.showinfo("Grading", "Absolute grading applied successfully.")


def relative_grading(conn, cursor, course_id):
    try:
        # Count how many marks entries exist for this course
        cursor.execute(
            "SELECT COUNT(*) FROM Results WHERE course_id = %s AND total_marks IS NOT NULL;",
            (course_id,),
        )
        count = cursor.fetchone()[0]

        if count < 2:
            messagebox.showwarning(
                "Grading Skipped",
                "Not enough students with marks to apply relative grading (need at least 2).",
            )
            return

        # Now calculate mean and stddev
        cursor.execute(
            "SELECT AVG(total_marks), STDDEV(total_marks) FROM Results WHERE course_id = %s;",
            (course_id,),
        )
        result = cursor.fetchone()

        if result and result[0] is not None and result[1] is not None:
            mean, stddev = result
            query = """
                UPDATE Results
                SET grade = CASE
                    WHEN total_marks >= %s + 1 * %s THEN 'A'
                    WHEN total_marks >= %s + 0.5 * %s THEN 'B'
                    WHEN total_marks >= %s - 0.5 * %s THEN 'C'
                    WHEN total_marks >= %s - 1 * %s THEN 'D'
                    ELSE 'F'
                END
                WHERE course_id = %s
            """
            params = (mean, stddev, mean, stddev, mean, stddev, mean, stddev, course_id)
            if execute_query(conn, cursor, query, params):
                messagebox.showinfo("Grading", "Relative grading applied successfully.")
        else:
            messagebox.showerror(
                "Grading Error", "Could not calculate mean and standard deviation."
            )
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Grading Error", f"Error in relative grading: {e}")


def plot_percentage_distribution(conn, cursor, course_id=None):
    if course_id:
        query = "SELECT total_marks FROM Results WHERE course_id = %s;"
        percentages = execute_query(conn, cursor, query, (course_id,), fetch=True)
    else:
        query = "SELECT total_marks FROM Results;"
        percentages = execute_query(conn, cursor, query, fetch=True)

    if percentages:
        data = np.array([p[0] for p in percentages if p[0] is not None])
        if data.size > 0:
            mean = np.mean(data)
            std_dev = np.std(data)
            plt.hist(
                data,
                bins=20,
                density=True,
                alpha=0.6,
                color="skyblue",
                edgecolor="black",
            )
            x = np.linspace(min(data), max(data), 100)
            y = (1 / (std_dev * np.sqrt(2 * np.pi))) * np.exp(
                -0.5 * ((x - mean) / std_dev) ** 2
            )
            plt.plot(x, y, color="red", linewidth=2)
            plt.title("Normal Distribution of Total Marks")
            plt.xlabel("Total Marks")
            plt.ylabel("Density")
            plt.grid(True)
            plt.show()
        else:
            messagebox.showinfo("Plot", "No valid percentage data to plot.")
    else:
        messagebox.showinfo("Plot", "No results found to plot.")


def insert_record(conn, cursor, table, columns, values):
    placeholders = ", ".join(["%s"] * len(values))
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders});"
    return execute_query(conn, cursor, query, values)


def update_record(
    conn, cursor, table, columns, values, condition_column, condition_value
):
    set_clause = ", ".join([f"{col} = %s" for col in columns])
    query = f"UPDATE {table} SET {set_clause} WHERE {condition_column} = %s;"
    return execute_query(conn, cursor, query, values + [condition_value])


def delete_record(conn, cursor, table, condition_column, condition_value):
    query = f"DELETE FROM {table} WHERE {condition_column} = %s;"
    return execute_query(conn, cursor, query, (condition_value,))


class LMSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Learning Management System")
        self.conn, self.cursor = connect_db()
        if not self.conn:
            return
        self.user = None
        self._execute_code1()
        self.show_login_menu()

    def _execute_code1(self):
        user_script = """CREATE TABLE IF NOT EXISTS Users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'instructor', 'admin'))
        );"""
        execute_query(self.conn, self.cursor, user_script)

        student_script = """CREATE TABLE IF NOT EXISTS Students (
            program VARCHAR(50),
            semester INT
        ) INHERITS (Users);"""
        execute_query(self.conn, self.cursor, student_script)

        instructor_script = """CREATE TABLE IF NOT EXISTS Instructors (
            department VARCHAR(100),
            designation VARCHAR(50)
        ) INHERITS (Users);"""
        execute_query(self.conn, self.cursor, instructor_script)

        admin_script = """CREATE TABLE IF NOT EXISTS Admins (
            role_description TEXT
        ) INHERITS (Users);"""
        execute_query(self.conn, self.cursor, admin_script)

        courses_script = """CREATE TABLE IF NOT EXISTS Courses (
            course_id SERIAL PRIMARY KEY NOT NULL,
            title VARCHAR(100) NOT NULL,
            credit_hours INT NOT NULL CHECK (credit_hours BETWEEN 1 AND 4),
            instructor_id INT,
            semester VARCHAR(20),
            FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, courses_script)

        course_prerequisite_script = """CREATE TABLE IF NOT EXISTS CoursePrerequisites (
            course_id INT NOT NULL,
            prerequisite_id INT NOT NULL,
            PRIMARY KEY (course_id, prerequisite_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
            FOREIGN KEY (prerequisite_id) REFERENCES Courses(course_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, course_prerequisite_script)

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
        execute_query(self.conn, self.cursor, registration_script)

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
            UNIQUE (user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, result_script)

        attendance_script = """CREATE TABLE IF NOT EXISTS Attendance (
            attendance_id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            course_id INT NOT NULL,
            date DATE NOT NULL,
            status VARCHAR(10) CHECK (status IN ('present', 'absent', 'late')) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, attendance_script)

        bugs_script = """CREATE TABLE IF NOT EXISTS bug (
            bug_id SERIAL PRIMARY KEY,
            sender_id INT NOT NULL,
            Description TEXT NOT NULL,
            status VARCHAR(10) CHECK (status IN ('open', 'in_progress', 'closed')) NOT NULL,
            Time TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, bugs_script)

        rechecking_script = """CREATE TABLE IF NOT EXISTS rechecking (
            recheck_id SERIAL PRIMARY KEY,
            sender_id INT NOT NULL,
            course_id INT NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exam_type VARCHAR(20) CHECK (exam_type IN ('quiz', 'mid term', 'final')) NOT NULL,
            status VARCHAR(10) CHECK (status IN ('pending', 'approved', 'rejected')) NOT NULL,
            FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, rechecking_script)

        calendar_script = """CREATE TABLE IF NOT EXISTS academic_calendar (
            event_id SERIAL PRIMARY KEY,
            event_name VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            event_date DATE
        );"""
        execute_query(self.conn, self.cursor, calendar_script)

        feedback_script = """CREATE TABLE IF NOT EXISTS feedback (
            feedback_id SERIAL PRIMARY KEY,
            sender_id INT NOT NULL,
            course_id INT NOT NULL,
            instructor_id INT,
            rating INT CHECK (rating BETWEEN 1 AND 5),
            comments TEXT,
            time TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
            FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, feedback_script)

        update_rechecking_status_script = """ UPDATE rechecking
        SET status = CASE
                            WHEN status = 'pending' AND CURRENT_TIMESTAMP - created_at > INTERVAL '10 days' THEN 'rejected'
                            WHEN status = 'pending' AND CURRENT_TIMESTAMP - created_at > INTERVAL '7 days' THEN 'approved'
                            ELSE status
                        END
        WHERE status = 'pending';
        """
        execute_query(self.conn, self.cursor, update_rechecking_status_script)

        discussion_script = """CREATE TABLE IF NOT EXISTS DiscussionThreads (
            thread_id SERIAL PRIMARY KEY,
            course_id INT NOT NULL,
            instructor_id INT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deleted', 'locked', 'archived')),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
            FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, discussion_script)

        reply_script = """CREATE TABLE IF NOT EXISTS DiscussionReplies (
            reply_id SERIAL PRIMARY KEY,
            thread_id INT NOT NULL,
            sender_id INT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (thread_id) REFERENCES DiscussionThreads(thread_id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE
        );"""
        execute_query(self.conn, self.cursor, reply_script)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_menu(self):
        self.clear_window()
        title_label = ttk.Label(
            self.root, text="Welcome to the LMS", font=("Arial", 16)
        )
        title_label.pack(pady=20)

        login_user_button = ttk.Button(
            self.root, text="Login as User", command=self.login_user
        )
        login_user_button.pack(pady=10)

        login_admin_button = ttk.Button(
            self.root, text="Login as Admin", command=self.login_admin
        )
        login_admin_button.pack(pady=10)

        login_instructor_button = ttk.Button(
            self.root, text="Login as Instructor", command=self.login_instructor
        )
        login_instructor_button.pack(pady=10)

        register_user_button = ttk.Button(
            self.root, text="Register", command=self.show_registration_form
        )
        register_user_button.pack(pady=10)

        exit_button = ttk.Button(self.root, text="Exit", command=self.root.destroy)
        exit_button.pack(pady=10)

    def login_user(self):
        self.show_login_form("user")

    def login_admin(self):
        self.show_login_form("admin")

    def login_instructor(self):
        self.show_login_form("instructor")

    def show_login_form(self, role):
        self.clear_window()
        title_label = ttk.Label(
            self.root, text=f"Login as {role.capitalize()}", font=("Arial", 14)
        )
        title_label.pack(pady=20)

        email_label = ttk.Label(self.root, text="Email:")
        email_label.pack()
        self.email_entry = ttk.Entry(self.root)
        self.email_entry.pack(pady=5)

        password_label = ttk.Label(self.root, text="Password:")
        password_label.pack()
        self.password_entry = ttk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        login_button = ttk.Button(
            self.root, text="Login", command=self.authenticate_user
        )
        login_button.pack(pady=10)

        back_button = ttk.Button(
            self.root, text="Back to Menu", command=self.show_login_menu
        )
        back_button.pack(pady=10)

    def authenticate_user(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        if not email or not password:
            messagebox.showerror("Login Error", "Please enter both email and password.")
            return

        query = """SELECT user_id, name, role FROM Users WHERE email = %s AND password = %s"""

        self.cursor.execute(query, (email, password))
        user_data = self.cursor.fetchone()

        if user_data:
            self.user_id, self.user_name, self.role = user_data
            if self.role not in ["student", "admin", "instructor"]:
                messagebox.showerror("Login Error", "Invalid role assigned to user.")
                return
            messagebox.showinfo("Login Successful", f"Welcome, {self.user_name}!")
            self.show_user_menu()
        else:
            self.role = None  # Ensure self.role is set to None if login fails
            messagebox.showerror("Login Error", "Invalid email or password.")

    def show_user_menu(self):
        self.clear_window()

        if self.role.strip().lower() == "student":
            menu_label = ttk.Label(self.root, text="Student's Menu", font=("Arial", 16))
            menu_label.pack(pady=20)
            ttk.Button(self.root, text="View Courses", command=self.view_courses).pack(
                pady=5
            )
            ttk.Button(
                self.root, text="View Academic Calendar", command=self.view_calendar
            ).pack(pady=5)
            ttk.Button(self.root, text="View Grades", command=self.view_grades).pack(
                pady=5
            )
            ttk.Button(
                self.root, text="View Attendance", command=self.view_attendance
            ).pack(pady=5)
            ttk.Button(
                self.root, text="Request Rechecking", command=self.request_rechecking
            ).pack(pady=5)
            ttk.Button(
                self.root, text="Give Feedback", command=self.give_feedback
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="View Discussion Threads",
                command=self.view_discussion_threads,
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="Reply to Discussion Thread",
                command=self.reply_to_thread,
            ).pack(pady=5)
            ttk.Button(self.root, text="Report a Bug", command=self.report_bug).pack(
                pady=5
            )
            ttk.Button(self.root, text="Logout", command=self.show_login_menu).pack(
                pady=10
            )

        elif self.role.strip().lower() == "admin":
            menu_label = ttk.Label(self.root, text="Admin Section", font=("Arial", 16))
            menu_label.pack(pady=10)
            ttk.Button(self.root, text="Manage Users", command=self.manage_users).pack(
                pady=5
            )
            ttk.Button(
                self.root, text="Manage Courses", command=self.manage_courses
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="View Rechecking Requests",
                command=self.view_rechecking_requests,
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="View Percentage Distribution",
                command=lambda: plot_percentage_distribution(self.conn, self.cursor),
            ).pack(pady=5)
            ttk.Button(
                self.root, text="View Feedback", command=self.view_feedback
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="Update Academic Calendar",
                command=self.insert_calendar_event,
            ).pack(pady=5)
            ttk.Button(self.root, text="Report a Bug", command=self.report_bug).pack(
                pady=5
            )
            ttk.Button(self.root, text="Logout", command=self.show_login_menu).pack(
                pady=10
            )

        elif self.role.strip().lower() == "instructor":
            menu_label = ttk.Label(
                self.root, text="Instructor's Section", font=("Arial", 16)
            )
            menu_label.pack(pady=20)
            ttk.Button(self.root, text="Add Mark", command=self.add_marks).pack(pady=5)
            ttk.Button(
                self.root, text="Apply Grading", command=self.show_grading_options
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="View Rechecking Requests",
                command=self.view_rechecking_requests,
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="View Percentage Distribution",
                command=lambda: plot_percentage_distribution(self.conn, self.cursor),
            ).pack(pady=5)
            ttk.Button(
                self.root, text="View Academic Calendar", command=self.view_calendar
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="Create Discussion Thread",
                command=self.create_discussion_thread,
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="View Discussion Threads",
                command=self.view_discussion_threads,
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="Reply to Discussion Thread",
                command=self.reply_to_thread,
            ).pack(pady=5)
            ttk.Button(self.root, text="Report a Bug", command=self.report_bug).pack(
                pady=5
            )
            ttk.Button(self.root, text="Logout", command=self.show_login_menu).pack(
                pady=10
            )

    def report_bug(self):
        bug_window = tk.Toplevel(self.root)
        bug_window.title("Report a Bug")

        ttk.Label(bug_window, text="Describe the bug:").pack(pady=5)
        bug_text = tk.Text(bug_window, height=10, width=50)
        bug_text.pack(pady=5)

        def submit_bug():
            description = bug_text.get("1.0", tk.END).strip()
            if description:
                query = """INSERT INTO bug (sender_id, Description, status, Time)
                    VALUES (%s, %s, 'open', NOW())  -- status is 'open' by default, Time is NOW()
                """
                params = (self.user_id, description)
                if execute_query(self.conn, self.cursor, query, params):
                    messagebox.showinfo(
                        "Bug Reported", "Thank you for reporting the bug!"
                    )
                    bug_window.destroy()
                else:
                    messagebox.showerror("Error", "Failed to report bug.")
            else:
                messagebox.showerror("Error", "Please describe the bug.")

        ttk.Button(bug_window, text="Submit Bug Report", command=submit_bug).pack(
            pady=10
        )

    def show_registration_form(self):
        self.clear_window()
        title_label = ttk.Label(self.root, text="User Registration", font=("Arial", 14))
        title_label.pack(pady=20)

        name_label = ttk.Label(self.root, text="Name:")
        name_label.pack()
        self.name_entry = ttk.Entry(self.root)
        self.name_entry.pack(pady=5)

        email_label = ttk.Label(self.root, text="Email:")
        email_label.pack()
        self.reg_email_entry = ttk.Entry(self.root)
        self.reg_email_entry.pack(pady=5)

        password_label = ttk.Label(self.root, text="Password:")
        password_label.pack()
        self.reg_password_entry = ttk.Entry(self.root, show="*")
        self.reg_password_entry.pack(pady=5)

        role_label = ttk.Label(self.root, text="Role:")
        role_label.pack()
        self.role_var = tk.StringVar(value="student")  # Default to student
        student_radio = ttk.Radiobutton(
            self.root, text="Student", variable=self.role_var, value="student"
        )
        instructor_radio = ttk.Radiobutton(
            self.root, text="Instructor", variable=self.role_var, value="instructor"
        )
        admin_radio = ttk.Radiobutton(
            self.root, text="Admin", variable=self.role_var, value="admin"
        )
        student_radio.pack(anchor=tk.W)
        instructor_radio.pack(anchor=tk.W)
        admin_radio.pack(anchor=tk.W)

        register_button = ttk.Button(
            self.root, text="Register", command=self.register_user
        )
        register_button.pack(pady=10)

        back_button = ttk.Button(
            self.root, text="Back to Menu", command=self.show_login_menu
        )
        back_button.pack(pady=10)

    def register_user(self):
        name = self.name_entry.get()
        email = self.reg_email_entry.get()
        password = self.reg_password_entry.get()
        role = self.role_var.get()

        if not name or not email or not password or not role:
            messagebox.showerror("Registration Error", "All fields are required.")
            return

        # Basic email validation
        if "@" not in email:
            messagebox.showerror("Registration Error", "Invalid email address.")
            return

        # Check if email already exists
        check_email_query = "SELECT email FROM Users WHERE email = %s"
        self.cursor.execute(check_email_query, (email,))
        if self.cursor.fetchone():
            messagebox.showerror(
                "Registration Error", "Email address already registered."
            )
            return

        # Insert new user into the appropriate table based on role
        try:
            if role == "student":
                insert_user_query = """INSERT INTO Students (name, email, password, role, program, semester)
                    VALUES (%s, %s, %s, %s, NULL, NULL)
                """
            elif role == "instructor":
                insert_user_query = """INSERT INTO Instructors (name, email, password, role, department, designation)
                    VALUES (%s, %s, %s, %s, NULL, NULL)
                """
            elif role == "admin":
                insert_user_query = """INSERT INTO Admins (name, email, password, role, role_description)
                    VALUES (%s, %s, %s, %s, NULL)
                """
            else:
                messagebox.showerror("Registration Error", "Invalid role selected.")
                return

            self.cursor.execute(insert_user_query, (name, email, password, role))
            self.conn.commit()
            messagebox.showinfo(
                "Registration Successful",
                "You have been successfully registered. Please log in.",
            )
            self.show_login_menu()  # Go back to login menu
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Registration Error", f"Failed to register user: {e}")
            return

    def add_marks(self):
        self.clear_window()
        ttk.Label(self.root, text="Add Marks", font=("Arial", 16)).pack(pady=20)

        course_label = ttk.Label(self.root, text="Course:")
        course_label.pack()
        self.add_marks_course_var = tk.StringVar()
        self.add_marks_course_combobox = ttk.Combobox(
            self.root, textvariable=self.add_marks_course_var
        )
        self.populate_course_combobox(self.add_marks_course_combobox)
        self.add_marks_course_combobox.pack(pady=5)

        student_label = ttk.Label(self.root, text="Student ID:")
        student_label.pack()
        self.add_marks_student_entry = ttk.Entry(self.root)
        self.add_marks_student_entry.pack(pady=5)

        for label_text, attr in [
            ("Quiz 1 Marks:", "quiz1"),
            ("Quiz 2 Marks:", "quiz2"),
            ("Midterm Marks:", "midterm"),
            ("Final Marks:", "final"),
        ]:
            label = ttk.Label(self.root, text=label_text)
            label.pack()
            entry = ttk.Entry(self.root)
            setattr(self, f"add_marks_{attr}_entry", entry)
            entry.pack(pady=5)

        submit_button = ttk.Button(
            self.root, text="Submit Marks", command=self.submit_marks
        )
        submit_button.pack(pady=10)

        back_button = ttk.Button(
            self.root, text="Back to Menu", command=self.show_user_menu
        )
        back_button.pack(pady=10)

    def submit_marks(self):
        course_id = self.add_marks_course_var.get().split("(")[-1].split(")")[0]
        student_id = self.add_marks_student_entry.get()
        quiz1 = self.add_marks_quiz1_entry.get()
        quiz2 = self.add_marks_quiz2_entry.get()
        midterm = self.add_marks_midterm_entry.get()
        final = self.add_marks_final_entry.get()

        if not (course_id and student_id and quiz1 and quiz2 and midterm and final):
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            quiz1 = float(quiz1)
            quiz2 = float(quiz2)
            midterm = float(midterm)
            final = float(final)
            total_marks = quiz1 + quiz2 + midterm + final

            query = """INSERT INTO Results (user_id, course_id, quiz1, quiz2, midterm, final, total_marks)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (user_id, course_id) DO UPDATE
                   SET quiz1 = EXCLUDED.quiz1,
                       quiz2 = EXCLUDED.quiz2,
                       midterm = EXCLUDED.midterm,
                       final = EXCLUDED.final,
                       total_marks = EXCLUDED.total_marks"""
            params = (student_id, course_id, quiz1, quiz2, midterm, final, total_marks)

            if execute_query(self.conn, self.cursor, query, params):
                messagebox.showinfo("Success", "Marks submitted successfully.")
                self.show_user_menu()
            else:
                messagebox.showerror("Error", "Failed to submit marks.")
        except ValueError:
            messagebox.showerror("Error", "Marks must be numeric values.")

    def show_grading_options(self):
        grading_window = tk.Toplevel(self.root)
        grading_window.title("Apply Grading")

        ttk.Label(grading_window, text="Select Course:", font=("Arial", 12)).pack(
            pady=5
        )

        # Fetch courses from the database to populate the dropdown
        query = "SELECT course_id, title FROM Courses"
        courses = execute_query(self.conn, self.cursor, query, fetch=True)
        if not courses:
            messagebox.showerror("Error", "No courses found.")
            grading_window.destroy()
            return

        course_names = [f"{title} ({course_id})" for course_id, title in courses]
        self.selected_course_var = tk.StringVar()
        course_dropdown = ttk.Combobox(
            grading_window, textvariable=self.selected_course_var, values=course_names
        )
        course_dropdown.pack(pady=5)

        ttk.Label(
            grading_window, text="Choose Grading Method:", font=("Arial", 12)
        ).pack(pady=10)

        ttk.Button(
            grading_window,
            text="Absolute Grading",
            command=lambda: self.apply_grading_and_save(
                absolute_grading, self.selected_course_var.get()
            ),
        ).pack(pady=5)

        ttk.Button(
            grading_window,
            text="Relative Grading",
            command=lambda: self.apply_grading_and_save(
                relative_grading, self.selected_course_var.get()
            ),
        ).pack(pady=5)

    def apply_grading_and_save(self, grading_function, selected_course_name):
        if not selected_course_name:
            messagebox.showerror("Error", "Please select a course.")
            return

        # Extract course_id from the selected course name
        course_id = selected_course_name.split("(")[-1].split(")")[0]

        # Apply the selected grading method (this updates the grade column)
        grading_function(self.conn, self.cursor, course_id)

    def view_courses(self):
        self.clear_window()
        ttk.Label(self.root, text="View Courses", font=("Arial", 16)).pack(pady=20)
        query = """SELECT c.course_id, c.title, c.credit_hours, u.name as instructor_name
            FROM Courses c
            JOIN Users u ON c.instructor_id = u.user_id
        """
        courses = execute_query(self.conn, self.cursor, query, fetch=True)
        if courses:
            for course in courses:
                course_info = f"Course ID: {course[0]}, Title: {course[1]}, Credits: {course[2]}, Instructor: {course[3]}"
                ttk.Label(self.root, text=course_info).pack(pady=2)
        else:
            ttk.Label(self.root, text="No courses found.").pack(pady=10)
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=10
        )

    def view_grades(self):
        self.clear_window()
        ttk.Label(self.root, text="View Grades", font=("Arial", 16)).pack(pady=20)
        query = """SELECT c.title, r.quiz1, r.quiz2, r.midterm, r.final, r.total_marks, r.grade
            FROM Results r
            JOIN Courses c ON r.course_id = c.course_id
            WHERE r.user_id = %s
        """
        grades = execute_query(
            self.conn, self.cursor, query, (self.user_id,), fetch=True
        )
        if grades:
            for grade in grades:
                grade_info = f"Course: {grade[0]}, Quiz 1: {grade[1]}, Quiz 2: {grade[2]}, Midterm: {grade[3]}, Final: {grade[4]}, Total Marks: {grade[5]}, Grade: {grade[6]}"
                ttk.Label(self.root, text=grade_info).pack(pady=2)
        else:
            ttk.Label(self.root, text="No grades found.").pack(pady=10)
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=10
        )

    def view_attendance(self):
        self.clear_window()
        ttk.Label(self.root, text="View Attendance", font=("Arial", 16)).pack(pady=20)
        query = """SELECT c.title, a.date, a.status
            FROM Attendance a
            JOIN Courses c ON a.course_id = c.course_id
            WHERE a.user_id = %s
        """
        attendance_records = execute_query(
            self.conn, self.cursor, query, (self.user_id,), fetch=True
        )
        if attendance_records:
            for record in attendance_records:
                attendance_info = (
                    f"Course: {record[0]}, Date: {record[1]}, Status: {record[2]}"
                )
                ttk.Label(self.root, text=attendance_info).pack(pady=2)
        else:
            ttk.Label(self.root, text="No attendance records found.").pack(pady=10)
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=10
        )

    def request_rechecking(self):
        self.clear_window()
        ttk.Label(self.root, text="Request Rechecking", font=("Arial", 16)).pack(
            pady=20
        )

        ttk.Label(self.root, text="Course ID:").pack()
        self.recheck_course_id_var = tk.StringVar()
        ttk.Entry(self.root, textvariable=self.recheck_course_id_var).pack(pady=5)

        ttk.Label(self.root, text="Exam Type:").pack()
        self.recheck_exam_type_var = tk.StringVar()
        self.recheck_exam_type_combobox = ttk.Combobox(
            self.root,
            textvariable=self.recheck_exam_type_var,
            values=["quiz", "mid term", "final"],
            state="readonly",
        )
        self.recheck_exam_type_combobox.pack(pady=5)

        ttk.Label(self.root, text="Reason:").pack()
        self.recheck_reason_text = tk.Text(self.root, height=5, width=40)
        self.recheck_reason_text.pack(pady=5)

        ttk.Button(
            self.root, text="Submit Request", command=self.submit_recheck_request
        ).pack(pady=10)
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=10
        )

    def submit_recheck_request(self):
        try:
            course_id = int(self.recheck_course_id_var.get().strip())
        except ValueError:
            messagebox.showerror("Rechecking Request", "Course ID must be an integer.")
            return

        exam_type = self.recheck_exam_type_var.get().strip().lower()
        reason = self.recheck_reason_text.get("1.0", tk.END).strip()

        if not course_id or not exam_type or not reason:
            messagebox.showerror("Rechecking Request", "Please fill in all fields.")
            return

        query = """INSERT INTO rechecking (sender_id, course_id, reason, exam_type, status)
               VALUES (%s, %s, %s, %s, 'pending')"""
        params = (self.user_id, course_id, reason, exam_type)

        if execute_query(self.conn, self.cursor, query, params):
            messagebox.showinfo(
                "Rechecking Request", "Your request has been submitted."
            )
            self.show_user_menu()
        else:
            messagebox.showerror(
                "Rechecking Request",
                "Failed to submit request. Check console for details.",
            )

    def populate_course_combobox(self, combobox=None):
        query = "SELECT course_id, title FROM Courses"
        courses = execute_query(self.conn, self.cursor, query, fetch=True)
        if courses:
            course_list = [f"{title} ({course_id})" for course_id, title in courses]
            if combobox:
                combobox["values"] = course_list
            else:
                self.recheck_course_combobox["values"] = course_list
        else:

            if combobox:
                combobox["values"] = []
            else:
                self.recheck_course_combobox["values"] = []

    def manage_users(self):
        self.clear_window()
        ttk.Label(self.root, text="Manage Users", font=("Arial", 16)).pack(pady=20)
        # Add functionality to view, add, edit, and delete users
        ttk.Button(self.root, text="View Users", command=self.view_users).pack(pady=5)
        ttk.Button(self.root, text="Add User", command=self.add_user).pack(pady=5)
        ttk.Button(self.root, text="Edit User", command=self.edit_user).pack(pady=5)
        ttk.Button(self.root, text="Delete User", command=self.delete_user).pack(pady=5)
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=10
        )

    def view_users(self):
        self.clear_window()
        ttk.Label(self.root, text="View Users", font=("Arial", 16)).pack(pady=20)
        query = "SELECT user_id, name, email, role FROM Users"
        users = execute_query(self.conn, self.cursor, query, fetch=True)
        if users:
            for user in users:
                user_info = (
                    f"ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}"
                )
                ttk.Label(self.root, text=user_info).pack(pady=2)
        else:
            ttk.Label(self.root, text="No users found.").pack(pady=10)
        ttk.Button(
            self.root, text="Back to Manage Users", command=self.manage_users
        ).pack(pady=10)

    def add_user(self):
        self.clear_window()
        ttk.Label(self.root, text="Add User", font=("Arial", 16)).pack(pady=20)

        name_label = ttk.Label(self.root, text="Name:")
        name_label.pack()
        self.add_name_entry = ttk.Entry(self.root)
        self.add_name_entry.pack(pady=5)

        email_label = ttk.Label(self.root, text="Email:")
        email_label.pack()
        self.add_email_entry = ttk.Entry(self.root)
        self.add_email_entry.pack(pady=5)

        password_label = ttk.Label(self.root, text="Password:")
        password_label.pack()
        self.add_password_entry = ttk.Entry(self.root, show="*")
        self.add_password_entry.pack(pady=5)

        role_label = ttk.Label(self.root, text="Role:")
        role_label.pack()
        self.add_role_var = tk.StringVar(value="student")
        role_frame = ttk.Frame(self.root)
        role_frame.pack(pady=5)
        student_radio = ttk.Radiobutton(
            role_frame, text="Student", variable=self.add_role_var, value="student"
        )
        instructor_radio = ttk.Radiobutton(
            role_frame,
            text="Instructor",
            variable=self.add_role_var,
            value="instructor",
        )
        admin_radio = ttk.Radiobutton(
            role_frame, text="Admin", variable=self.add_role_var, value="admin"
        )
        student_radio.pack(side=tk.LEFT, padx=10)
        instructor_radio.pack(side=tk.LEFT, padx=10)
        admin_radio.pack(side=tk.LEFT, padx=10)

        def add_user_to_db():
            name = self.add_name_entry.get()
            email = self.add_email_entry.get()
            password = self.add_password_entry.get()
            role = self.add_role_var.get()
            if name and email and password and role:
                if "@" not in email:
                    messagebox.showerror("Add User Error", "Invalid email format.")
                    return
                query = "INSERT INTO Users (name, email, password, role) VALUES (%s, %s, %s, %s)"
                params = (name, email, password, role)
                if execute_query(self.conn, self.cursor, query, params):
                    messagebox.showinfo("Add User", "User added successfully.")
                    self.manage_users()
                else:
                    messagebox.showerror("Add User Error", "Failed to add user.")
            else:
                messagebox.showerror("Add User Error", "All fields are required.")

        add_button = ttk.Button(self.root, text="Add User", command=add_user_to_db)
        add_button.pack(pady=10)
        back_button = ttk.Button(
            self.root, text="Back to Manage Users", command=self.manage_users
        )
        back_button.pack(pady=10)

    def edit_user(self):
        self.clear_window()
        ttk.Label(self.root, text="Edit User", font=("Arial", 16)).pack(pady=20)

        user_id_label = ttk.Label(self.root, text="User ID to Edit:")
        user_id_label.pack()
        self.edit_user_id_entry = ttk.Entry(self.root)
        self.edit_user_id_entry.pack(pady=5)

        name_label = ttk.Label(self.root, text="New Name:")
        name_label.pack()
        self.edit_name_entry = ttk.Entry(self.root)
        self.edit_name_entry.pack(pady=5)

        email_label = ttk.Label(self.root, text="New Email:")
        email_label.pack()
        self.edit_email_entry = ttk.Entry(self.root)
        self.edit_email_entry.pack(pady=5)

        password_label = ttk.Label(self.root, text="New Password:")
        password_label.pack()
        self.edit_password_entry = ttk.Entry(self.root, show="*")
        self.edit_password_entry.pack(pady=5)

        role_label = ttk.Label(self.root, text="New Role:")
        role_label.pack()
        self.edit_role_var = tk.StringVar()
        student_radio = ttk.Radiobutton(
            self.root, text="Student", variable=self.edit_role_var, value="student"
        )
        instructor_radio = ttk.Radiobutton(
            self.root,
            text="Instructor",
            variable=self.edit_role_var,
            value="instructor",
        )
        admin_radio = ttk.Radiobutton(
            self.root, text="Admin", variable=self.edit_role_var, value="admin"
        )
        student_radio.pack(anchor=tk.W)
        instructor_radio.pack(anchor=tk.W)
        admin_radio.pack(anchor=tk.W)

        def update_user_in_db():
            user_id = self.edit_user_id_entry.get()
            name = self.edit_name_entry.get()
            email = self.edit_email_entry.get()
            password = self.edit_password_entry.get()
            role = self.edit_role_var.get()

            if user_id:
                update_fields = {}
                update_values = []
                if name:
                    update_fields["name"] = name
                    update_values.append(name)
                if email:
                    if "@" not in email:
                        messagebox.showerror("Edit User Error", "Invalid email format.")
                        return
                    update_fields["email"] = email
                    update_values.append(email)
                if password:
                    update_fields["password"] = password
                    update_values.append(password)
                if role:
                    update_fields["role"] = role
                    update_values.append(role)

                if update_fields:
                    columns = list(update_fields.keys())
                    values = update_values
                    if update_record(
                        self.conn,
                        self.cursor,
                        "Users",
                        columns,
                        values,
                        "user_id",
                        user_id,
                    ):
                        messagebox.showinfo("Edit User", "User updated successfully.")
                        self.manage_users()
                    else:
                        messagebox.showerror(
                            "Edit User Error", "Failed to update user."
                        )
                else:
                    messagebox.showinfo("Edit User", "No fields to update.")
            else:
                messagebox.showerror("Edit User Error", "User ID is required.")

        update_button = ttk.Button(
            self.root, text="Update User", command=update_user_in_db
        )
        update_button.pack(pady=10)
        back_button = ttk.Button(
            self.root, text="Back to Manage Users", command=self.manage_users
        )
        back_button.pack(pady=10)

    def delete_user(self):
        self.clear_window()
        ttk.Label(self.root, text="Delete User", font=("Arial", 16)).pack(pady=20)

        user_id_label = ttk.Label(self.root, text="User ID to Delete:")
        user_id_label.pack()
        self.delete_user_id_entry = ttk.Entry(self.root)
        self.delete_user_id_entry.pack(pady=5)

        def delete_user_from_db():
            user_id = self.delete_user_id_entry.get()
            if user_id:
                if delete_record(self.conn, self.cursor, "Users", "user_id", user_id):
                    messagebox.showinfo("Delete User", "User deleted successfully.")
                    self.manage_users()
                else:
                    messagebox.showerror("Delete User Error", "Failed to delete user.")
            else:
                messagebox.showerror("Delete User Error", "User ID is required.")

        delete_button = ttk.Button(
            self.root, text="Delete User", command=delete_user_from_db
        )
        delete_button.pack(pady=10)
        back_button = ttk.Button(
            self.root, text="Back to Manage Users", command=self.manage_users
        )
        back_button.pack(pady=10)

    def manage_courses(self):
        self.clear_window()
        ttk.Label(self.root, text="Manage Courses", font=("Arial", 16)).pack(pady=20)
        ttk.Button(self.root, text="View Courses", command=self.view_all_courses).pack(
            pady=5
        )
        ttk.Button(self.root, text="Add Course", command=self.add_course).pack(pady=5)
        ttk.Button(
            self.root, text="Edit Course", command=lambda: self.edit_course()
        ).pack(pady=5)
        ttk.Button(
            self.root, text="Delete Course", command=lambda: self.delete_course()
        ).pack(pady=5)
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=10
        )

    def view_all_courses(self):
        self.clear_window()
        ttk.Label(self.root, text="View All Courses", font=("Arial", 16)).pack(pady=20)
        query = """SELECT c.course_id, c.title, c.credit_hours, u.name as instructor_name, c.semester
            FROM Courses c
            JOIN Users u ON c.instructor_id = u.user_id
        """
        courses = execute_query(self.conn, self.cursor, query, fetch=True)
        if courses:
            for course in courses:
                course_info = f"ID: {course[0]}, Title: {course[1]}, Credits: {course[2]}, Instructor: {course[3]}, Semester: {course[4]}"
                ttk.Label(self.root, text=course_info).pack(pady=2)
        else:
            ttk.Label(self.root, text="No courses found.").pack(pady=10)
        ttk.Button(
            ttk.Button(
                self.root, text="Back to Manage Courses", command=self.manage_courses
            ).pack(pady=10)
        ).pack(pady=10)

    def add_course_to_db(self):
        course_id = self.add_course_id_entry.get()
        title = self.add_course_title_entry.get()
        credit_hours = self.add_course_credit_hours_entry.get()
        selected_instructor = self.add_course_instructor_var.get()
        semester = self.add_course_semester_entry.get()

        if course_id and title and credit_hours and selected_instructor and semester:
            try:
                credit_hours = int(credit_hours)
                if not (1 <= credit_hours <= 4):
                    messagebox.showerror(
                        "Add Course Error", "Credit hours must be between 1 and 4."
                    )
                    return
                instructor_id = selected_instructor.split("(")[-1].split(")")[
                    0
                ]  # Extract instructor_id
                # Check if the instructor_id exists (though the dropdown should prevent invalid entries)
                query_check_instructor = "SELECT user_id FROM Users WHERE user_id = %s AND role = 'instructor'"
                self.cursor.execute(query_check_instructor, (instructor_id,))
                if not self.cursor.fetchone():
                    messagebox.showerror(
                        "Add Course Error", "Selected instructor is invalid."
                    )
                    return

                query_insert_course = "INSERT INTO Courses (course_id, title, credit_hours, instructor_id, semester) VALUES (%s, %s, %s, %s, %s)"
                params = (course_id, title, credit_hours, instructor_id, semester)
                if execute_query(self.conn, self.cursor, query_insert_course, params):
                    messagebox.showinfo("Add Course", "Course added successfully.")
                    self.manage_courses()
                else:
                    messagebox.showerror("Add Course Error", "Failed to add course.")
            except ValueError:
                messagebox.showerror(
                    "Add Course Error", "Invalid input for credit hours."
                )
                return
        else:
            messagebox.showerror("Add Course Error", "All fields are required.")

        add_button = ttk.Button(
            self.root, text="Add Course", command=self.add_course_to_db
        )
        add_button.pack(pady=10)
        back_button = ttk.Button(
            self.root, text="Back to Manage Courses", command=self.manage_courses
        )
        back_button.pack(pady=10)

        # Call this here to ensure the dropdown is populated when the form is shown
        self.populate_instructor_dropdown(self.add_course_instructor_combobox)

    def get_course_id(self):
        try:
            return int(self.edit_course_id_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Course ID must be an integer.")
            messagebox.showerror(
                "Error", "Invalid Course ID. Please enter a valid integer."
            )
        return None

    def edit_course(self):
        self.clear_window()
        ttk.Label(self.root, text="Edit Course", font=("Arial", 16)).pack(pady=20)

        course_id_label = ttk.Label(self.root, text="Course ID to Edit:")
        self.edit_course_id_entry = ttk.Entry(self.root)
        self.edit_course_id_entry.pack(pady=5)

        course_id_label.pack()
        self.edit_course_id_entry = ttk.Entry(self.root)
        self.edit_course_id_entry.pack(pady=5)

        title_label = ttk.Label(self.root, text="New Title:")
        title_label.pack()
        self.edit_course_title_entry = ttk.Entry(self.root)
        self.edit_course_title_entry.pack(pady=5)

        credits_label = ttk.Label(self.root, text="New Credit Hours:")
        credits_label.pack()
        self.edit_course_credits_entry = ttk.Entry(self.root)
        self.edit_course_credits_entry.pack(pady=5)

        instructor_label = ttk.Label(self.root, text="New Instructor:")
        instructor_label.pack()
        self.edit_course_instructor_var = tk.StringVar()
        self.edit_course_instructor_combobox = ttk.Combobox(
            self.root, textvariable=self.edit_course_instructor_var
        )
        self.populate_instructor_combobox(self.edit_course_instructor_combobox)
        self.edit_course_instructor_combobox.pack(pady=5)

        semester_label = ttk.Label(self.root, text="New Semester:")
        semester_label.pack()
        self.edit_course_semester_entry = ttk.Entry(self.root)
        self.edit_course_semester_entry.pack(pady=5)

        ttk.Button(
            self.root, text="Save Changes", command=self.save_course_changes
        ).pack(pady=10)

        back_button = ttk.Button(
            self.root, text="Back to Manage Courses", command=self.manage_courses
        )
        back_button.pack(pady=10)

        def update_course_in_db():
            course_id = self.edit_course_id_entry.get()
            title = self.edit_course_title_entry.get()
            credits = self.edit_course_credits_entry.get()
            instructor_name = self.edit_course_instructor_var.get()
            semester = self.edit_course_semester_entry.get()

            if course_id:
                update_fields = {}
                update_values = []
                if title:
                    update_fields["title"] = title
                    update_values.append(title)
                if credits:
                    try:
                        credits = int(credits)
                        if not (1 <= credits <= 4):
                            messagebox.showerror(
                                "Edit Course Error",
                                "Credit hours must be between 1 and 4.",
                            )
                            return
                        update_fields["credit_hours"] = credits
                        update_values.append(credits)
                    except ValueError:
                        messagebox.showerror(
                            "Edit Course Error", "Credit hours must be a number."
                        )
                        return
                if instructor_name:
                    query = "SELECT user_id FROM Users WHERE name = %s"
                    self.cursor.execute(query, (instructor_name,))
                    instructor_id_result = self.cursor.fetchone()
                    if instructor_id_result:
                        instructor_id = instructor_id_result[0]
                        update_fields["instructor_id"] = instructor_id
                        update_values.append(instructor_id)
                    else:
                        messagebox.showerror(
                            "Edit Course Error",
                            "Instructor not found. Please select a valid instructor.",
                        )
                        return
                if semester:
                    update_fields["semester"] = semester
                    update_values.append(semester)

                if update_fields:
                    columns = list(update_fields.keys())
                    values = update_values
                    if update_record(
                        self.conn,
                        self.cursor,
                        "Courses",
                        columns,
                        values,
                        "course_id",
                        course_id,
                    ):
                        messagebox.showinfo(
                            "Edit Course", "Course updated successfully."
                        )
                        self.manage_courses()
                    else:
                        messagebox.showerror(
                            "Edit Course Error", "Failed to update course."
                        )
                else:
                    messagebox.showinfo("Edit Course", "No fields to update.")
            else:
                messagebox.showerror("Edit Course Error", "Course ID is required.")

        update_button = ttk.Button(
            self.root, text="Update Course", command=update_course_in_db
        )
        update_button.pack(pady=10)
        back_button = ttk.Button(
            self.root, text="Back to Manage Courses", command=self.manage_courses
        )
        back_button.pack(pady=10)

    def delete_course(self):
        self.clear_window()
        ttk.Label(self.root, text="Delete Course", font=("Arial", 16)).pack(pady=20)

        course_id_label = ttk.Label(self.root, text="Course ID to Delete:")
        course_id_label.pack()
        self.delete_course_id_entry = ttk.Entry(self.root)
        self.delete_course_id_entry.pack(pady=5)

        def delete_course_from_db():
            course_id = self.delete_course_id_entry.get()
            if course_id:
                if delete_record(
                    self.conn, self.cursor, "Courses", "course_id", course_id
                ):
                    messagebox.showinfo("Delete Course", "Course deleted successfully.")
                    self.manage_courses()
                else:
                    messagebox.showerror(
                        "Delete Course Error", "Failed to delete course."
                    )
            else:
                messagebox.showerror("Delete Course Error", "Course ID is required.")

        delete_button = ttk.Button(
            self.root, text="Delete Course", command=delete_course_from_db
        )
        delete_button.pack(pady=10)
        back_button = ttk.Button(
            self.root, text="Back to Manage Courses", command=self.manage_courses
        )
        back_button.pack(pady=10)

    def save_course_changes(self):
        try:
            course_id = self.edit_course_id_entry.get()
            new_title = self.edit_course_title_entry.get()
            new_credits = int(self.edit_course_credits_entry.get())
            new_semester = self.edit_course_semester_entry.get()
            instructor_key = self.edit_course_instructor_var.get()
            instructor_id = self.instructor_map.get(instructor_key)

            if not (new_title and new_credits and new_semester and instructor_id):
                messagebox.showerror("Error", "All fields are required.")
                return

            query = """UPDATE Courses
                       SET title = %s, credit_hours = %s, semester = %s, instructor_id = %s
                       WHERE course_id = %s"""
            params = (new_title, new_credits, new_semester, instructor_id, course_id)
            success = execute_query(self.conn, self.cursor, query, params)

            if success:
                messagebox.showinfo("Success", "Course updated successfully.")
                self.manage_courses()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update course: {e}")

    def view_rechecking_requests(self):
        self.clear_window()
        ttk.Label(self.root, text="View Rechecking Requests", font=("Arial", 16)).pack(
            pady=20
        )
        query = """SELECT * FROM Rechecking"""
        requests = execute_query(self.conn, self.cursor, query, fetch=True)
        if requests:
            for request in requests:
                request_info = f"ID: {request[0]}, Student: {request[1]}, Course: {request[2]}, Exam Type: {request[3]}, Reason: {request[4]}, Status: {request[5]}, Requested At: {request[6]}"
                ttk.Label(self.root, text=request_info).pack(pady=2)
        else:
            ttk.Label(self.root, text="No rechecking requests found.").pack(pady=10)
            ttk.Button(
                self.root, text="Back to Menu", command=self.show_user_menu
            ).pack(pady=10)

    def submit_feedback(self):
        self.clear_window()
        ttk.Label(self.root, text="Submit Course Feedback", font=("Arial", 16)).pack(
            pady=20
        )

        # Course ID
        ttk.Label(self.root, text="Course ID:").pack()
        self.feedback_course_id_var = tk.StringVar()
        ttk.Entry(self.root, textvariable=self.feedback_course_id_var).pack(pady=5)

        # Instructor ID
        ttk.Label(self.root, text="Instructor ID:").pack()
        self.feedback_instructor_id_var = tk.StringVar()
        ttk.Entry(self.root, textvariable=self.feedback_instructor_id_var).pack(pady=5)

        # Rating (1 to 5)
        ttk.Label(self.root, text="Rating (1-5):").pack()
        self.feedback_rating_var = tk.IntVar()
        ttk.Spinbox(
            self.root, from_=1, to=5, textvariable=self.feedback_rating_var, width=5
        ).pack(pady=5)

        # Comments
        ttk.Label(self.root, text="Comments:").pack()
        self.feedback_comments_text = tk.Text(self.root, height=5, width=40)
        self.feedback_comments_text.pack(pady=5)

        # Submit and Back Buttons
        ttk.Button(self.root, text="Submit", command=self.insert_feedback).pack(pady=10)
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=5
        )

    def insert_feedback(self):
        try:
            course_id = int(self.feedback_course_id_var.get())
            instructor_id = int(self.feedback_instructor_id_var.get())
            rating = self.feedback_rating_var.get()
        except ValueError:
            messagebox.showerror(
                "Feedback", "Course ID and Instructor ID must be integers."
            )
            return

        comments = self.feedback_comments_text.get("1.0", tk.END).strip()

        if not course_id or not instructor_id or not rating or not comments:
            messagebox.showerror("Feedback", "Please fill in all fields.")
            return

        if not (1 <= rating <= 5):
            messagebox.showerror("Feedback", "Rating must be between 1 and 5.")
            return

        query = """INSERT INTO feedback (sender_id, course_id, instructor_id, rating, comments, time)
               VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)"""
        params = (self.user_id, course_id, instructor_id, rating, comments)
        if execute_query(self.conn, self.cursor, query, params):
            messagebox.showinfo("Feedback", "Feedback submitted successfully!")
            self.show_user_menu()
        else:
            messagebox.showerror("Feedback", "Failed to submit feedback.")

    def insert_calendar_event(self):
        self.clear_window()
        ttk.Label(
            self.root, text="Add Academic Calendar Event", font=("Arial", 16)
        ).pack(pady=20)

        # Event Name
        ttk.Label(self.root, text="Event Name:").pack()
        self.event_name_var = tk.StringVar()
        ttk.Entry(self.root, textvariable=self.event_name_var).pack(pady=5)

        # Description
        ttk.Label(self.root, text="Description:").pack()
        self.event_description_text = tk.Text(self.root, height=5, width=40)
        self.event_description_text.pack(pady=5)

        # Event Date (YYYY-MM-DD)
        ttk.Label(self.root, text="Event Date (YYYY-MM-DD):").pack()
        self.event_date_var = tk.StringVar()
        ttk.Entry(self.root, textvariable=self.event_date_var).pack(pady=5)

        # Buttons
        ttk.Button(self.root, text="Add Event", command=self.save_calendar_event).pack(
            pady=10
        )
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=5
        )

    def save_calendar_event(self):
        name = self.event_name_var.get().strip()
        description = self.event_description_text.get("1.0", tk.END).strip()
        date_str = self.event_date_var.get().strip()

        if not name or not description or not date_str:
            messagebox.showerror("Calendar Event", "Please fill in all fields.")
            return

        # Validate date format
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Calendar Event", "Date must be in YYYY-MM-DD format.")
            return

        query = """INSERT INTO academic_calendar (event_name, description, event_date)
               VALUES (%s, %s, %s)"""
        params = (name, description, date_str)

        if execute_query(self.conn, self.cursor, query, params):
            messagebox.showinfo("Calendar Event", "Event added successfully!")
            self.show_user_menu()
        else:
            messagebox.showerror("Calendar Event", "Failed to add event.")

    def view_calendar(self):
        self.clear_window()
        ttk.Label(self.root, text="Academic Calendar", font=("Arial", 16)).pack(pady=20)

        query = """SELECT event_name, description, event_date FROM academic_calendar"""
        events = execute_query(self.conn, self.cursor, query, fetch=True)

        if events:
            for event in events:
                event_info = (
                    f"Event: {event[0]}, Description: {event[1]}, Date: {event[2]}"
                )
                ttk.Label(self.root, text=event_info).pack(pady=2)
        else:
            ttk.Label(self.root, text="No events found in the calendar.").pack(pady=10)

        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=5
        )

    def create_discussion_thread(self):
        self.clear_window()
        ttk.Label(self.root, text="Create Discussion Thread", font=("Arial", 16)).pack(
            pady=10
        )

        ttk.Label(self.root, text="Course ID:").pack()
        self.course_id_var = tk.StringVar()
        ttk.Entry(self.root, textvariable=self.course_id_var).pack(pady=5)

        ttk.Label(self.root, text="Message:").pack()
        self.message_text = tk.Text(self.root, height=5, width=40)
        self.message_text.pack(pady=5)

        ttk.Button(
            self.root, text="Post Thread", command=self.submit_discussion_thread
        ).pack(pady=10)
        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack()

    def submit_discussion_thread(self):
        try:
            course_id = int(self.course_id_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Course ID must be an integer.")
            return

        message = self.message_text.get("1.0", tk.END).strip()

        if not course_id or not message:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        query = """INSERT INTO DiscussionThreads (course_id, instructor_id, message)
               VALUES (%s, %s, %s)"""
        params = (course_id, self.user_id, message)
        if execute_query(self.conn, self.cursor, query, params):
            messagebox.showinfo("Success", "Discussion thread posted.")
            self.show_user_menu()
        else:
            messagebox.showerror("Database Error", "Failed to post thread.")

    def view_discussion_threads(self):
        self.clear_window()
        ttk.Label(self.root, text="Discussion Threads", font=("Arial", 16)).pack(
            pady=10
        )

        query = """SELECT d.thread_id, c.title, u.name, d.message, d.status, d.created_at
               FROM DiscussionThreads d
               JOIN Courses c ON d.course_id = c.course_id
               JOIN Users u ON d.instructor_id = u.user_id
               WHERE d.status = 'active' ORDER BY d.created_at DESC"""
        threads = execute_query(self.conn, self.cursor, query, fetch=True)

        if threads:
            for t in threads:
                info = f"ID: {t[0]} | Course: {t[1]} | Instructor: {t[2]}\nMessage: {t[3]}\nStatus: {t[4]} | Date: {t[5]}"
                ttk.Label(self.root, text=info, justify="left").pack(
                    anchor="w", padx=10, pady=5
                )
        else:
            ttk.Label(self.root, text="No active threads found.").pack(pady=10)

        ttk.Button(self.root, text="Back to Menu", command=self.show_user_menu).pack(
            pady=10
        )

    def reply_to_thread(self):
        self.clear_window()
        ttk.Label(self.root, text="Reply to a Thread", font=("Arial", 16)).pack(pady=10)

        ttk.Label(self.root, text="Thread ID:").pack()
        thread_id_entry = ttk.Entry(self.root)
        thread_id_entry.pack()

        ttk.Label(self.root, text="Your Message:").pack()
        message_entry = tk.Text(self.root, height=5, width=50)
        message_entry.pack()

        def submit_reply():
            thread_id = thread_id_entry.get()
            message = message_entry.get("1.0", tk.END).strip()
            if thread_id and message:
                query = """INSERT INTO DiscussionReplies (thread_id, sender_id, message)
                VALUES (%s, %s, %s)"""
                execute_query(
                    self.conn, self.cursor, query, (thread_id, self.user_id, message)
                )
                messagebox.showinfo("Success", "Reply posted.")
                self.show_user_menu()
            else:
                messagebox.showerror("Error", "Thread ID and message are required.")

        ttk.Button(self.root, text="Submit Reply", command=submit_reply).pack(pady=5)
        ttk.Button(self.root, text="Back", command=self.show_user_menu).pack(pady=5)

    def view_thread_replies(self, thread_id):
        self.clear_window()
        ttk.Label(
            self.root, text=f"Replies for Thread ID {thread_id}", font=("Arial", 16)
        ).pack(pady=10)

        query = """SELECT reply_id, sender_id, message, created_at
        FROM DiscussionReplies
        WHERE thread_id = %s
        ORDER BY created_at"""
        replies = execute_query(self.conn, self.cursor, query, (thread_id,), fetch=True)

        if replies:
            for reply in replies:
                reply_text = f"Reply ID: {reply[0]}, Sender: {reply[1]}, Time: {reply[3]}\n{reply[2]}"
                ttk.Label(
                    self.root, text=reply_text, wraplength=600, justify="left"
                ).pack(pady=4)
        else:
            ttk.Label(self.root, text="No replies yet.").pack(pady=5)

        ttk.Button(self.root, text="Back", command=self.show_user_menu).pack(pady=10)


# Starting the GUI Application
if __name__ == "__main__":
    root = tk.Tk()
    app = LMSApp(root)
    root.mainloop()
    root.destroy()
    if app.conn and app.cursor:
        close_db(
            app.conn, app.cursor
        )  # Close the database connection when the app is closed
