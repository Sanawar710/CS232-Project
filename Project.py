import tkinter as tk  # 'tkinter' is a standard GUI toolkit in Python.
from tkinter import ttk, messagebox  # 'ttk' is a themed widget set for tkinter.
import psycopg2 as pg  # 'psycopg2' is used to connect to PostgreSQL databases with Python.
import pandas as pd  # 'pandas' is a data manipulation and analysis library.
import matplotlib.pyplot as plt  # 'matplotlib' is a plotting library for Python.
import numpy as np  # 'numpy' is a library for numerical computations in Python.

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


def absolute_grading(conn, cursor):
    query = """UPDATE Results
    SET Grade = CASE
        WHEN total_marks >= 80 THEN 'A'
        WHEN total_marks >= 70 THEN 'B'
        WHEN total_marks >= 60 THEN 'C'
        WHEN total_marks >= 50 THEN 'D'
        ELSE 'F'
    END;
    """
    if execute_query(conn, cursor, query):
        messagebox.showinfo("Grading", "Absolute grading applied successfully.")


def relative_grading(conn, cursor):
    try:
        cursor.execute("SELECT AVG(total_marks), STDDEV(total_marks) FROM Results;")
        result = cursor.fetchone()
        if result and result[0] is not None and result[1] is not None:
            mean, stddev = result
            query = """UPDATE Results
                SET grade = CASE
                    WHEN total_marks >= %s + 1 * %s THEN 'A'
                    WHEN total_marks >= %s + 0.5 * %s THEN 'B'
                    WHEN total_marks >= %s - 0.5 * %s THEN 'C'
                    WHEN total_marks >= %s - 1 * %s THEN 'D'
                    ELSE 'F'
                END
            """
            params = (mean, stddev, mean, stddev, mean, stddev, mean, stddev)
            if execute_query(conn, cursor, query, params):
                messagebox.showinfo("Grading", "Relative grading applied successfully.")
        else:
            messagebox.showerror(
                "Grading Error", "Could not calculate mean and standard deviation."
            )
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Grading Error", f"Error in relative grading: {e}")


def plot_percentage_distribution(conn, cursor):
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
            plt.title("Normal Distribution of Total Percentages")
            plt.xlabel("Total Percentage")
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
        self.show_login_menu()

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

        exit_button = ttk.Button(self.root, text="Exit", command=self.root.destroy)
        exit_button.pack(pady=10)

    def login_user(self):
        self.show_login_form("user")

    def login_admin(self):
        self.show_login_form("admin")

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
        back_button.pack(pady=5)

    def authenticate_user(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        query = "SELECT user_id, name, email, role FROM Users WHERE email = %s AND password = %s"
        result = execute_query(
            self.conn, self.cursor, query, (email, password), fetch=True
        )
        if result:
            self.user_id, self.name, self.email, self.role = result[0]
            messagebox.showinfo(
                "Login Successful", f"Welcome, {self.name} ({self.role})!"
            )
            self.show_user_menu()
        else:
            messagebox.showerror(
                "Login Failed", "Invalid credentials. Please try again."
            )

    def show_user_menu(self):
        self.clear_window()
        menu_label = ttk.Label(self.root, text="User Menu", font=("Arial", 16))
        menu_label.pack(pady=20)

        if self.role == "student":
            ttk.Button(self.root, text="View Courses", command=self.view_courses).pack(
                pady=5
            )
            ttk.Button(self.root, text="View Grades", command=self.view_grades).pack(
                pady=5
            )
            ttk.Button(
                self.root, text="View Attendance", command=self.view_attendance
            ).pack(pady=5)
        elif self.role == "instructor":
            ttk.Button(self.root, text="View Courses", command=self.view_courses).pack(
                pady=5
            )
            ttk.Button(
                self.root, text="Manage Grades", command=self.manage_grades
            ).pack(pady=5)
            ttk.Button(
                self.root, text="View Student Attendance", command=self.view_attendance
            ).pack(pady=5)
        elif self.role == "admin":
            ttk.Button(self.root, text="Manage Users", command=self.manage_users).pack(
                pady=5
            )
            ttk.Button(
                self.root, text="Manage Courses", command=self.manage_courses
            ).pack(pady=5)
            ttk.Button(
                self.root, text="Apply Grading", command=self.show_grading_options
            ).pack(pady=5)
            ttk.Button(
                self.root,
                text="View Percentage Distribution",
                command=lambda: plot_percentage_distribution(self.conn, self.cursor),
            ).pack(pady=5)

        logout_button = ttk.Button(
            self.root, text="Logout", command=self.show_login_menu
        )
        logout_button.pack(pady=10)

    def show_grading_options(self):
        grading_window = tk.Toplevel(self.root)
        grading_window.title("Apply Grading")

        ttk.Button(
            grading_window,
            text="Absolute Grading",
            command=lambda: absolute_grading(self.conn, self.cursor),
        ).pack(pady=10, padx=20)
        ttk.Button(
            grading_window,
            text="Relative Grading",
            command=lambda: relative_grading(self.conn, self.cursor),
        ).pack(pady=10, padx=20)

    def view_courses(self):
        self.clear_window()
        title_label = ttk.Label(self.root, text="View Courses", font=("Arial", 14))
        title_label.pack(pady=10)

        if self.role == "student":
            query = """SELECT c.title, c.credit_hours, u.name AS instructor, c.semester
                       FROM Registrations r
                       JOIN Courses c ON r.course_id = c.course_id
                       JOIN Users u ON c.instructor_id = u.user_id
                       WHERE r.user_id = %s"""
            courses = execute_query(
                self.conn, self.cursor, query, (self.user_id,), fetch=True
            )
            if courses:
                self.display_table(
                    ["Title", "Credit Hours", "Instructor", "Semester"], courses
                )
            else:
                ttk.Label(self.root, text="No enrolled courses found.").pack(pady=10)
        elif self.role == "instructor":
            query = """SELECT c.title, c.credit_hours, c.semester
                       FROM Courses c
                       WHERE c.instructor_id = %s"""
            courses = execute_query(
                self.conn, self.cursor, query, (self.user_id,), fetch=True
            )
            if courses:
                self.display_table(["Title", "Credit Hours", "Semester"], courses)
            else:
                ttk.Label(self.root, text="No courses taught by you.").pack(pady=10)
        elif self.role == "admin":
            query = """SELECT c.course_id, c.title, c.credit_hours, u.name AS instructor, c.semester
                       FROM Courses c
                       LEFT JOIN Users u ON c.instructor_id = u.user_id"""
            courses = execute_query(self.conn, self.cursor, query, fetch=True)
            if courses:
                self.display_table(
                    ["Course ID", "Title", "Credit Hours", "Instructor", "Semester"],
                    courses,
                )
            else:
                ttk.Label(self.root, text="No courses in the system.").pack(pady=10)

        back_button = ttk.Button(
            self.root, text="Back to Menu", command=self.show_user_menu
        )
        back_button.pack(pady=10)

    def view_grades(self):
        self.clear_window()
        title_label = ttk.Label(self.root, text="View Grades", font=("Arial", 14))
        title_label.pack(pady=10)

        if self.role == "student":
            query = """SELECT c.title, r.quiz1, r.quiz2, r.midterm, r.final, r.total_marks, r.grade
                       FROM Results r
                       JOIN Courses c ON r.course_id = c.course_id
                       WHERE r.user_id = %s"""
            grades = execute_query(
                self.conn, self.cursor, query, (self.user_id,), fetch=True
            )
            if grades:
                self.display_table(
                    [
                        "Course",
                        "Quiz 1",
                        "Quiz 2",
                        "Midterm",
                        "Final",
                        "Total Marks",
                        "Grade",
                    ],
                    grades,
                )
            else:
                ttk.Label(self.root, text="No grades available.").pack(pady=10)
        elif self.role == "instructor":
            ttk.Label(self.root, text="Select a course to view student grades:").pack(
                pady=5
            )
            courses = execute_query(
                self.conn,
                self.cursor,
                "SELECT course_id, title FROM Courses WHERE instructor_id = %s",
                (self.user_id,),
                fetch=True,
            )
            if courses:
                course_var = tk.StringVar(self.root)
                course_var.set(courses[0][1])  # Default value
                course_dropdown = ttk.Combobox(
                    self.root,
                    textvariable=course_var,
                    values=[c[1] for c in courses],
                    state="readonly",
                )
                course_dropdown.pack(pady=5)
                view_button = ttk.Button(
                    self.root,
                    text="View Grades for Selected Course",
                    command=lambda: self.view_grades_for_course(course_var.get()),
                )
                view_button.pack(pady=5)
            else:
                ttk.Label(self.root, text="No courses taught by you.").pack(pady=10)
        elif self.role == "admin":
            query = """SELECT u.name AS student, c.title AS course, r.quiz1, r.quiz2, r.midterm, r.final, r.total_marks, r.grade
                       FROM Results r
                       JOIN Users u ON r.user_id = u.user_id
                       JOIN Courses c ON r.course_id = c.course_id"""
            all_grades = execute_query(self.conn, self.cursor, query, fetch=True)
            if all_grades:
                self.display_table(
                    [
                        "Student",
                        "Course",
                        "Quiz 1",
                        "Quiz 2",
                        "Midterm",
                        "Final",
                        "Total Marks",
                        "Grade",
                    ],
                    all_grades,
                )
            else:
                ttk.Label(self.root, text="No grades recorded.").pack(pady=10)

        back_button = ttk.Button(
            self.root, text="Back to Menu", command=self.show_user_menu
        )
        back_button.pack(pady=10)

    def view_grades_for_course(self, course_title):
        grades_window = tk.Toplevel(self.root)
        grades_window.title(f"Grades for {course_title}")
        query = """SELECT u.name AS student, r.quiz1, r.quiz2, r.midterm, r.final, r.total_marks, r.grade
                   FROM Results r
                   JOIN Users u ON r.user_id = u.user_id
                   JOIN Courses c ON r.course_id = c.course_id
                   WHERE c.title = %s AND c.instructor_id = %s"""
        course_data = execute_query(
            self.conn,
            self.cursor,
            "SELECT course_id FROM Courses WHERE title = %s AND instructor_id = %s",
            (course_title, self.user_id),
            fetch=True,
        )
        if course_data:
            course_id = course_data[0][0]
            grades = execute_query(
                self.conn, self.cursor, query, (course_title, self.user_id), fetch=True
            )
            if grades:
                self.display_table(
                    [
                        "Student",
                        "Quiz 1",
                        "Quiz 2",
                        "Midterm",
                        "Final",
                        "Total Marks",
                        "Grade",
                    ],
                    grades,
                    parent=grades_window,
                )
            else:
                ttk.Label(
                    grades_window, text="No grades recorded for this course."
                ).pack(pady=10)

            add_grade_button = ttk.Button(
                grades_window,
                text="Add/Update Grades",
                command=lambda: self.add_update_grades(course_id, grades_window),
            )
            add_grade_button.pack(pady=10)
        else:
            ttk.Label(grades_window, text="Course not found.").pack(pady=10)

    def add_update_grades(self, course_id, parent_window):
        grade_window = tk.Toplevel(parent_window)
        grade_window.title("Add/Update Grades")

        # Get list of students in the course
        student_query = """SELECT u.user_id, u.name FROM Users u
                           JOIN Registrations r ON u.user_id = r.user_id
                           WHERE r.course_id = %s AND r.status = 'enrolled'"""
        students = execute_query(
            self.conn, self.cursor, student_query, (course_id,), fetch=True
        )

        if not students:
            ttk.Label(grade_window, text="No students enrolled in this course.").pack(
                pady=10
            )
            return

        # Create a dictionary to store entry widgets for each student
        self.grade_entries = {}

        for student_id, student_name in students:
            ttk.Label(grade_window, text=f"Student: {student_name}").pack(pady=5)

            # Fetch existing grades if available
            existing_grade_query = "SELECT quiz1, quiz2, midterm, final FROM Results WHERE user_id = %s AND course_id = %s"
            existing_grade = execute_query(
                self.conn,
                self.cursor,
                existing_grade_query,
                (student_id, course_id),
                fetch=True,
            )
            quiz1_val, quiz2_val, midterm_val, final_val = 0, 0, 0, 0
            if existing_grade:
                quiz1_val, quiz2_val, midterm_val, final_val = existing_grade[0]

            ttk.Label(grade_window, text="Quiz 1:").pack()
            quiz1_entry = ttk.Entry(grade_window)
            quiz1_entry.insert(0, quiz1_val)
            quiz1_entry.pack(pady=2)

            ttk.Label(grade_window, text="Quiz 2:").pack()
            quiz2_entry = ttk.Entry(grade_window)
            quiz2_entry.insert(0, quiz2_val)
            quiz2_entry.pack(pady=2)

            ttk.Label(grade_window, text="Midterm:").pack()
            midterm_entry = ttk.Entry(grade_window)
            midterm_entry.insert(0, midterm_val)
            midterm_entry.pack(pady=2)

            ttk.Label(grade_window, text="Final:").pack()
            final_entry = ttk.Entry(grade_window)
            final_entry.insert(0, final_val)
            final_entry.pack(pady=2)

            self.grade_entries[student_id] = {
                "quiz1": quiz1_entry,
                "quiz2": quiz2_entry,
                "midterm": midterm_entry,
                "final": final_entry,
            }

        save_button = ttk.Button(
            grade_window,
            text="Save Grades",
            command=lambda: self.save_grades(course_id, grade_window),
        )
        save_button.pack(pady=10)

    def save_grades(self, course_id, parent_window):
        for student_id, entries in self.grade_entries.items():
            quiz1 = float(entries["quiz1"].get()) if entries["quiz1"].get() else 0
            quiz2 = float(entries["quiz2"].get()) if entries["quiz2"].get() else 0
            midterm = float(entries["midterm"].get()) if entries["midterm"].get() else 0
            final = float(entries["final"].get()) if entries["final"].get() else 0
            total_marks = quiz1 + quiz2 + midterm + final
            grade = self.calculate_grade(total_marks)

            # Check if the record exists, if it does, update, otherwise insert.
            check_query = (
                "SELECT COUNT(*) FROM Results WHERE user_id = %s AND course_id = %s"
            )
            self.cursor.execute(check_query, (student_id, course_id))
            exists = self.cursor.fetchone()[0]

            if exists > 0:
                update_query = """UPDATE Results SET quiz1 = %s, quiz2 = %s, midterm = %s, final = %s, total_marks = %s, grade = %s
                                  WHERE user_id = %s AND course_id = %s"""
                params = (
                    quiz1,
                    quiz2,
                    midterm,
                    final,
                    total_marks,
                    grade,
                    student_id,
                    course_id,
                )
                if not execute_query(self.conn, self.cursor, update_query, params):
                    messagebox.showerror("Error", "Failed to update grades.")
                    return
            else:
                insert_query = """INSERT INTO Results (user_id, course_id, quiz1, quiz2, midterm, final, total_marks, grade)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (
                    student_id,
                    course_id,
                    quiz1,
                    quiz2,
                    midterm,
                    final,
                    total_marks,
                    grade,
                )
                if not execute_query(self.conn, self.cursor, insert_query, params):
                    messagebox.showerror("Error", "Failed to insert grades.")
                    return

        messagebox.showinfo("Success", "Grades saved successfully.")
        parent_window.destroy()

    def calculate_grade(self, total_marks):
        if total_marks >= 80:
            return "A"
        elif total_marks >= 70:
            return "B"
        elif total_marks >= 60:
            return "C"
        elif total_marks >= 50:
            return "D"
        else:
            return "F"

    def view_attendance(self):
        self.clear_window()
        title_label = ttk.Label(self.root, text="View Attendance", font=("Arial", 14))
        title_label.pack(pady=10)

        if self.role == "student":
            query = """SELECT c.title, a.date, a.status
                       FROM Attendance a
                       JOIN Courses c ON a.course_id = c.course_id
                       WHERE a.user_id = %s"""
            attendance = execute_query(
                self.conn, self.cursor, query, (self.user_id,), fetch=True
            )
            if attendance:
                self.display_table(["Course", "Date", "Status"], attendance)
            else:
                ttk.Label(self.root, text="No attendance records available.").pack(
                    pady=10
                )
        elif self.role == "instructor":
            ttk.Label(
                self.root, text="Select a course to view student attendance:"
            ).pack(pady=5)
            courses = execute_query(
                self.conn,
                self.cursor,
                "SELECT course_id, title FROM Courses WHERE instructor_id = %s",
                (self.user_id,),
                fetch=True,
            )
            if courses:
                course_var = tk.StringVar(self.root)
                course_var.set(courses[0][1])  # Default value
                course_dropdown = ttk.Combobox(
                    self.root,
                    textvariable=course_var,
                    values=[c[1] for c in courses],
                    state="readonly",
                )
                course_dropdown.pack(pady=5)
                view_button = ttk.Button(
                    self.root,
                    text="View Attendance for Selected Course",
                    command=lambda: self.view_attendance_for_course(course_var.get()),
                )
                view_button.pack(pady=5)
            else:
                ttk.Label(self.root, text="No courses taught by you.").pack(pady=10)
        elif self.role == "admin":
            query = """SELECT u.name AS student, c.title AS course, r.quiz1, r.quiz2, r.midterm, r.final, r.total_marks, r.grade
                       FROM Results r
                       JOIN Users u ON r.user_id = u.user_id
                       JOIN Courses c ON r.course_id = c.course_id"""
            all_grades = execute_query(self.conn, self.cursor, query, fetch=True)
        if all_grades:
            self.display_table(
                [
                    "Student",
                    "Course",
                    "Quiz 1",
                    "Quiz 2",
                    "Midterm",
                    "Final",
                    "Total Marks",
                    "Grade",
                ],
                all_grades,
            )
        else:
            ttk.Label(self.root, text="No grades recorded.").pack(pady=10)

        back_button = ttk.Button(
            self.root, text="Back to Menu", command=self.show_user_menu
        )
        back_button.pack(pady=10)

    def view_grades_for_course(self, course_title):
        grades_window = tk.Toplevel(self.root)
        grades_window.title(f"Grades for {course_title}")
        query = """SELECT u.name AS student, r.quiz1, r.quiz2, r.midterm, r.final, r.total_marks, r.grade
                   FROM Results r
                   JOIN Users u ON r.user_id = u.user_id
                   JOIN Courses c ON r.course_id = c.course_id
                   WHERE c.title = %s AND c.instructor_id = %s"""


# Starting the GUI Application
if __name__ == "__main__":
    root = tk.Tk()
    app = LMSApp(root)
    root.mainloop()
