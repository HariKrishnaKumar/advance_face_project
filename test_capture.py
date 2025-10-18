import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import os
import pandas as pd
import uuid

class RegistrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("User Registration")
        self.master.geometry("400x400")
        
        self.user_data = {}
        self.create_widgets()
    
    def create_widgets(self):
        fields = [
            ("Name", "entry"),
            ("Age", "spinbox"),
            ("Address", "entry"),
            ("Phone Number", "entry"),
            ("Department", "combobox")
        ]
        
        self.entries = {}
        
        for i, (text, field_type) in enumerate(fields):
            label = ttk.Label(self.master, text=text + ":")
            label.grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
            
            if field_type == "entry":
                entry = ttk.Entry(self.master)
                entry.grid(row=i, column=1, padx=10, pady=5, sticky=tk.EW)
                self.entries[text] = entry
            elif field_type == "spinbox":
                spinbox = ttk.Spinbox(self.master, from_=1, to=100)
                spinbox.grid(row=i, column=1, padx=10, pady=5, sticky=tk.EW)
                self.entries[text] = spinbox
            elif field_type == "combobox":
                dept = ttk.Combobox(self.master, values=["Sales", "IT", "HR", "Finance", "Operations",'others'])
                dept.grid(row=i, column=1, padx=10, pady=5, sticky=tk.EW)
                dept.current(0)
                self.entries[text] = dept
        
        submit_btn = ttk.Button(self.master, text="Submit", command=self.validate_registration)
        submit_btn.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.master.columnconfigure(1, weight=1)
    
    def validate_registration(self):
        required_fields = {
            "Name": self.entries["Name"].get(),
            "Age": self.entries["Age"].get(),
            "Address": self.entries["Address"].get(),
            "Phone Number": self.entries["Phone Number"].get(),
            "Department": self.entries["Department"].get()
        }
        
        for field, value in required_fields.items():
            if not value.strip():
                messagebox.showerror("Error", f"Please fill in {field} field")
                return
        
        try:
            age = int(required_fields["Age"])
            if not (1 <= age <= 100):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid age (1-100)")
            return
        
        self.user_data = required_fields
        self.user_data["Unique ID"] = str(uuid.uuid4())[:8].upper()  # Generate 8-character unique ID
        self.master.destroy()

class WebcamApp:
    def __init__(self, window, user_data):
        self.window = window
        self.user_data = user_data
        self.window.title(f"Webcam Photo Capture - {self.user_data['Name']}")
        
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "⚠️ Could not access webcam")
            self.window.destroy()
            return
        
        self.create_widgets()
        self.video_loop()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        self.video_label = ttk.Label(self.window)
        self.video_label.pack(padx=10, pady=10)
        
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10)
        
        self.capture_btn = ttk.Button(
            button_frame,
            text="Capture Photo",
            command=self.capture_photo
        )
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        
        self.exit_btn = ttk.Button(
            button_frame,
            text="Exit",
            command=self.on_close
        )
        self.exit_btn.pack(side=tk.LEFT, padx=5)
    
    def video_loop(self):
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        
        self.window.after(10, self.video_loop)
    
    def capture_photo(self):
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"{self.user_data['Unique ID']}_{timestamp}.jpg"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")],
                initialfile=default_name,
                title="Save Photo As"
            )
            
            if file_path:
                try:
                    img = Image.fromarray(frame_rgb)
                    img.save(file_path)
                    self.save_to_excel(file_path)
                    messagebox.showinfo(
                        "Success",
                        f"✓ Photo saved successfully!\n{file_path}"
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Error",
                        f"✗ Failed to save photo: {str(e)}"
                    )
    
    def save_to_excel(self, photo_path):
        excel_file = "user_credentials.xlsx"
        data = {
            "Unique ID": [self.user_data["Unique ID"]],
            "Name": [self.user_data["Name"]],
            "Age": [self.user_data["Age"]],
            "Address": [self.user_data["Address"]],
            "Phone Number": [self.user_data["Phone Number"]],
            "Department": [self.user_data["Department"]],
            "Photo Path": [photo_path],
            "Registration Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        }
        
        df = pd.DataFrame(data)
        
        if os.path.exists(excel_file):
            with pd.ExcelWriter(excel_file, mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
                df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
        else:
            df.to_excel(excel_file, index=False)
    
    def on_close(self):
        if self.cap.isOpened():
            self.cap.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    reg_window = RegistrationWindow(root)
    root.mainloop()
    
    if hasattr(reg_window, 'user_data') and reg_window.user_data:
        main_root = tk.Tk()
        app = WebcamApp(main_root, reg_window.user_data)
        main_root.mainloop()

# conformation message
print(f"\n✅ Success! User '{name}' has been registered with ID: {unique_id}")
print(f"Text details have been saved to the 'users' table in the database.")
print(f"Photo saved as: {photo_path}")

    


# Added a RegistrationWindow class that collects user information before accessing the webcam

# Implemented input validation for registration fields

# Added UUID generation for unique user identification

# Integrated Excel file storage using pandas

# Modified the photo naming convention to include the unique ID

# Added user information and photo path to Excel records

# Improved error handling and data validation

# Features:

# Registration requires all fields to be filled

# Age validation (1-100)

# Department selection from dropdown list

# Automatic generation of 8-character unique ID

# Excel file creation/updating with user data and photo paths

# Timestamped registration records

# Unique photo filenames incorporating user ID and timestamp

# To use this code:

# Install required packages: pip install opencv-python pandas pillow openpyxl

# Run the script

# Complete the registration form

# Capture photos which will be saved with user-specific information

# Check the generated user_credentials.xlsx file for all records

# The Excel file will contain:

# Unique ID

# User information

# Photo path

# Registration timestamp

# Photo capture timestamp (in filename)