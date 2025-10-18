import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import mediapipe as mp
from deepface import DeepFace
import numpy as np
import threading
import mysql.connector
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hari2003',
    'database': 'face_analysis_db'
}

class FaceAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Analysis System")
        self.root.geometry("1280x720")
        self.root.configure(bg='#2c3e50')

        # Initialize video capture
        self.cap = cv2.VideoCapture(0)

        # Connect to MySQL
        self.db_connection = mysql.connector.connect(**DB_CONFIG)
        self.create_database_table()

        # Setup GUI
        self.setup_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_gui(self):
        self.video_frame = ttk.LabelFrame(self.root, text="Live Camera Feed", width=800, height=600)
        self.video_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.info_frame = ttk.Frame(self.root, width=400, height=600)
        self.info_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH)

        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack()

        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.7)

        self.matched_face_label = ttk.Label(self.info_frame)
        self.matched_face_label.pack(pady=10)

        self.analysis_tree = ttk.Treeview(self.info_frame, columns=('Value'), show='headings', height=5)
        self.analysis_tree.heading('#0', text='Attribute')
        self.analysis_tree.heading('Value', text='Value')
        self.analysis_tree.column('#0', width=120)
        self.analysis_tree.column('Value', width=200)
        self.analysis_tree.tag_configure('header', background='#3498db', foreground='white')
        self.analysis_tree.pack(fill=tk.BOTH, expand=True)

        self.stats_button = ttk.Button(self.info_frame, text="Show Stats", command=self.show_stats_menu)
        self.stats_button.pack(pady=10)

        self.update_video()

    def create_database_table(self):
        cursor = self.db_connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_analysis (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                age INT,
                gender VARCHAR(50),
                emotion VARCHAR(50),
                timestamp DATETIME
            )
        """)
        self.db_connection.commit()
        cursor.close()

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            analysis_results = {}

            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    x = int(bbox.xmin * iw)
                    y = int(bbox.ymin * ih)
                    w = int(bbox.width * iw)
                    h = int(bbox.height * ih)

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    face_roi = frame[y:y + h, x:x + w]

                    try:
                        dfs = DeepFace.find(
                            img_path=face_roi,
                            db_path="db",
                            enforce_detection=False,
                            silent=True
                        )

                        analysis = DeepFace.analyze(
                            img_path=face_roi,
                            actions=['age', 'gender', 'emotion'],
                            enforce_detection=False,
                            silent=True,
                            detector_backend='mtcnn'
                        )

                        if isinstance(analysis, list):
                            analysis = analysis[0]

                        gender = max(analysis['gender'].items(), key=lambda x: x[1])[0] \
                            if isinstance(analysis['gender'], dict) else analysis['gender']
                        emotion = max(analysis['emotion'].items(), key=lambda x: x[1])[0]
                        name = 'Unknown'

                        if dfs and not dfs[0].empty:
                            best_match = dfs[0].iloc[0]
                            name = best_match['identity'].split('/')[-1]
                            self.update_matched_face(best_match['identity'])
                            self.save_to_database(name, analysis['age'], gender, emotion)

                        analysis_results = {
                            'Age': analysis['age'],
                            'Gender': gender,
                            'Emotion': emotion,
                            'Name': name
                        }

                    except Exception as e:
                        print(f"Analysis error: {e}")

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            self.update_analysis_tree(analysis_results)

        self.root.after(10, self.update_video)

    def update_matched_face(self, image_path):
        try:
            img = Image.open(image_path).resize((150, 150))
            imgtk = ImageTk.PhotoImage(img)
            self.matched_face_label.imgtk = imgtk
            self.matched_face_label.configure(image=imgtk)
        except Exception as e:
            print(f"Matched face display error: {e}")

    def update_analysis_tree(self, data):
        for i in self.analysis_tree.get_children():
            self.analysis_tree.delete(i)
        for key, value in data.items():
            self.analysis_tree.insert('', 'end', text=key, values=(value,))

    def save_to_database(self, name, age, gender, emotion):
        cursor = self.db_connection.cursor()
        cursor.execute("""
            INSERT INTO face_analysis (name, age, gender, emotion, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, age, gender, emotion, datetime.now()))
        self.db_connection.commit()
        cursor.close()

    def show_stats_menu(self):
        stats_win = tk.Toplevel(self.root)
        stats_win.title("Statistics Menu")
        stats_win.geometry("400x200")

        ttk.Label(stats_win, text="Choose a stats option:").pack(pady=10)

        ttk.Button(stats_win, text="Show All Stats", command=self.show_all_data).pack(pady=5)
        ttk.Button(stats_win, text="Show Per Person Stats", command=self.show_person_stats).pack(pady=5)

    def show_all_data(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT gender, emotion FROM face_analysis")
        rows = cursor.fetchall()
        cursor.close()

        genders = [row[0] for row in rows]
        emotions = [row[1] for row in rows]

        gender_counts = Counter(genders)
        emotion_counts = Counter(emotions)

        fig, axs = plt.subplots(1, 2, figsize=(10, 4))
        axs[0].bar(gender_counts.keys(), gender_counts.values(), color='skyblue')
        axs[0].set_title("Gender Distribution")

        axs[1].bar(emotion_counts.keys(), emotion_counts.values(), color='salmon')
        axs[1].set_title("Emotion Distribution")

        stats_fig = tk.Toplevel(self.root)
        stats_fig.title("Overall Stats")
        canvas = FigureCanvasTkAgg(fig, master=stats_fig)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def show_person_stats(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT name, emotion FROM face_analysis")
        rows = cursor.fetchall()
        cursor.close()

        person_emotions = {}
        for name, emotion in rows:
            person_emotions.setdefault(name, []).append(emotion)

        stats_fig = tk.Toplevel(self.root)
        stats_fig.title("Per Person Emotion Stats")

        fig, ax = plt.subplots(figsize=(10, 5))
        for name, emotions in person_emotions.items():
            emotion_counts = Counter(emotions)
            ax.bar([f"{name}\n{emo}" for emo in emotion_counts], emotion_counts.values(), label=name)

        ax.set_title("Emotions per Person")
        ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1))
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=stats_fig)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def on_close(self):
        self.cap.release()
        self.db_connection.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceAnalysisApp(root)
    root.mainloop()
