import tkinter as tk
from tkinter import ttk  # Import ttk for the Combobox widget
import subprocess
import sys
import mysql.connector
from datetime import datetime

# -----------------------------------------------------------------------------
# !             Database and Timetable Functions
# -----------------------------------------------------------------------------

def get_db_connection():
    """Function to create and return a database connection."""
    try:
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="hari2003",
            database="std_db"
        )
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def get_current_session():
    """Fetches the current session from the timetable."""
    conn = get_db_connection()
    if conn is None:
        return "DB connection failed", []

    cursor = conn.cursor()
    now = datetime.now()
    current_day = now.strftime('%A')
    current_time = now.strftime('%H:%M:%S')

    query = "SELECT subject_name, semester FROM timetable WHERE day_of_week = %s AND start_time <= %s AND end_time >= %s"
    cursor.execute(query, (current_day, current_time, current_time))
    sessions = cursor.fetchall()
    cursor.close()
    conn.close()

    if len(sessions) == 1:
        return f"Current Session: {sessions[0][0]}", [f"{s[0]} (Sem {s[1]})" for s in sessions]
    elif len(sessions) > 1:
        return "Multiple sessions found!", [f"{s[0]} (Sem {s[1]})" for s in sessions]
    else:
        return "No active session.", []


def run_script(filename):
    """Function to run a Python script."""
    try:
        subprocess.run([sys.executable, filename])
    except FileNotFoundError:
        print(f"Error: The file {filename} does not exist.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# -----------------------------------------------------------------------------
# !             Main Application Window
# -----------------------------------------------------------------------------

root = tk.Tk()
root.title("Attendance System")
root.geometry("350x400")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill='both')

label = tk.Label(frame, text="Select an option to run:")
label.pack(pady=(0, 10))

# --- New User Button ---
button1 = tk.Button(
    frame,
    text="New User Registration",
    command=lambda: run_script("test_capture.py"),
    width=25,
    padx=10,
    pady=5
)
button1.pack(pady=5)

# --- Survival Mode Button (assuming it's a different feature) ---
button2 = tk.Button(
    frame,
    text="Survival Mode",
    command=lambda: run_script("perefect_working.py"),
    width=25,
    padx=10,
    pady=5
)
button2.pack(pady=5)

# --- Timetable Integration Section ---
session_label_text, session_list = get_current_session()
session_label = tk.Label(frame, text=session_label_text)
session_label.pack(pady=(20, 5))

# --- Manual Override Dropdown ---
manual_selection_label = tk.Label(frame, text="Manual Override:")
manual_selection_label.pack(pady=(10, 0))
selected_session = tk.StringVar()
session_dropdown = ttk.Combobox(frame, textvariable=selected_session, width=22)
if session_list:
    session_dropdown['values'] = session_list
    session_dropdown.set(session_list[0]) # Default to the first detected session
session_dropdown.pack(pady=5)


# --- Attendance Mode Button ---
button3 = tk.Button(
    frame,
    text="Mark Attendance",
    command=lambda: run_script("timetable_integration.py"), # Runs the new script
    width=25,
    padx=10,
    pady=5,
    bg="lightblue"
)
button3.pack(pady=10)


root.mainloop()