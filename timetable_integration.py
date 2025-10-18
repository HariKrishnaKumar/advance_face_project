import cv2
import mysql.connector
from datetime import datetime
from deepface import DeepFace
import time as t

# -----------------------------------------------------------------------------
# !             SETUP: Connect to MySQL Database
# -----------------------------------------------------------------------------

def get_db_connection():
    """Function to create and return a database connection."""
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="hari2003",  # Make sure to use a secure way to handle passwords
        database="std_db"
    )

# -----------------------------------------------------------------------------
# !             Timetable Logic
# -----------------------------------------------------------------------------

def get_current_session(cursor):
    """
    Checks the timetable for the current session based on the current day and time.
    """
    now = datetime.now()
    current_day = now.strftime('%A')  # e.g., Monday, Tuesday
    current_time = now.strftime('%H:%M:%S')

    query = """
        SELECT subject_name, semester
        FROM timetable
        WHERE day_of_week = %s AND start_time <= %s AND end_time >= %s
    """
    cursor.execute(query, (current_day, current_time, current_time))
    sessions = cursor.fetchall()
    return sessions

# -----------------------------------------------------------------------------
# MAIN LOOP: Process Video Frames and Save Data to MySQL
# -----------------------------------------------------------------------------

def run_attendance():
    """Main function to run the attendance system."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current session
    sessions = get_current_session(cursor)
    current_subject = None
    current_semester = None

    if len(sessions) == 1:
        current_subject, current_semester = sessions[0]
        print(f"Current session detected: {current_subject} (Semester: {current_semester})")
    elif len(sessions) > 1:
        # If multiple sessions are found, prompt for selection (in a real UI)
        print("Multiple overlapping sessions detected. Please select one:")
        for i, (subject, semester) in enumerate(sessions):
            print(f"{i + 1}: {subject} (Semester: {semester})")
        # For this script, we'll just pick the first one as an example
        current_subject, current_semester = sessions[0]
        print(f"Auto-selected: {current_subject}")
    else:
        print("No active session found in the timetable. Running in manual mode.")
        # In a real UI, you would allow manual selection here.
        # For this script, we can default to a general attendance record.
        current_subject = "General"
        current_semester = 0

    cap = cv2.VideoCapture(0)
    registered_names = set()

    print("Streaming started. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            results = DeepFace.find(frame, db_path="db", enforce_detection=False)
            if results and len(results) > 0:
                df = results[0]
                if not df.empty:
                    top_match = df.iloc[0]
                    identity = top_match["identity"]
                    similarity = top_match.get("VGG-Face_cosine", "N/A")

                    if identity not in registered_names:
                        registered_names.add(identity)
                        now = datetime.now()
                        date_str = now.strftime("%Y-%m-%d")
                        time_str = now.strftime("%H:%M:%S")

                        query = """
                            INSERT INTO records (identity, similarity, date, time, subject_name, semester)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        values = (identity, str(similarity), date_str, time_str, current_subject, current_semester)
                        cursor.execute(query, values)
                        conn.commit()

                        print(f"Registered: {identity} for {current_subject} | Similarity: {similarity}")
                    else:
                        print(f"{identity} has already been registered in this session.")
        except Exception as e:
            # This will prevent the program from crashing if no face is detected
            pass
            
        cv2.imshow("Attendance System", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q')):
            break

    cap.release()
    cv2.destroyAllWindows()
    cursor.close()
    conn.close()

    print("Attendance records saved to the database.")

if __name__ == "__main__":
    run_attendance()