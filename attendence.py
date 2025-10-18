# This is the working program of the project for mysql

import cv2
import mysql.connector
from datetime import datetime
from deepface import DeepFace

# -----------------------------------------------------------------------------
# !             SETUP: Connect to MySQL Database
# -----------------------------------------------------------------------------

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Hari2003",
    database="std_db"
)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS records (
        id INT AUTO_INCREMENT PRIMARY KEY,
        identity VARCHAR(255),
        similarity VARCHAR(255),
        date DATE,
        time TIME
    )
''')
conn.commit()

# -----------------------------------------------------------------------------
# Initialize Webcam and Variables
# -----------------------------------------------------------------------------

cap = cv2.VideoCapture(0)
registered_names = set()

print("Streaming started. Press 'q' to quit.")

# -----------------------------------------------------------------------------
# MAIN LOOP: Process Video Frames and Save Data to MySQL
# -----------------------------------------------------------------------------

while True:
    ret, frame = cap.read()
    if not ret:
        break

    try:
        # Use DeepFace.find to detect and match faces in the current frame.
        results = DeepFace.find(frame, db_path="db", enforce_detection=False)
        print("DeepFace results:", results)  # Debug
        
        if results and len(results) > 0:
            df = results[0]
            print("DeepFace DataFrame:", df.head())  # Debug
            
            if not df.empty:
                top_match = df.iloc[0]
                identity = top_match["identity"]
                similarity = top_match.get("VGG-Face_cosine", "N/A")

                now = datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                time_str = now.strftime("%H:%M:%S")

                # Use this check if you want to insert only one record per identity per session.
                if identity not in registered_names:
                    registered_names.add(identity)

                    query = """
                        INSERT INTO records (identity, similarity, date, time)
                        VALUES (%s, %s, %s, %s)
                    """
                    values = (identity, similarity, date_str, time_str)
                    cursor.execute(query, values)
                    conn.commit()

                    print(f"Registered: {identity} | Similarity: {similarity} | {date_str} {time_str}")
                else:
                    print(f"{identity} has already been registered in this session.")
            else:
                print("No faces detected in the DataFrame.")
        else:
            print("DeepFace.find returned empty results.")

    except Exception as e:
        print("DeepFace error:", e)

    cv2.imshow("Capturing", frame)
    key = cv2.waitKey(1) & 0xFF
    if key in (ord('q'), ord('Q')):
        break

# -----------------------------------------------------------------------------
# CLEANUP: Release Resources
# -----------------------------------------------------------------------------

cap.release()
cv2.destroyAllWindows()
cursor.close()
conn.close()

print("Records successfully saved to the MySQL database.")
