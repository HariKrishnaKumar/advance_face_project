-- Create database
CREATE DATABASE IF NOT EXISTS std_db;
USE std_db;

-- Table for user registration (from test_capture.py)
-- This table stores information about the registered users.
CREATE TABLE IF NOT EXISTS users (
    unique_id VARCHAR(8) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    address VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    department VARCHAR(50) NOT NULL,
    photo_path VARCHAR(255) UNIQUE NOT NULL,
    registration_date DATETIME NOT NULL
);

-- Table for attendance records (from attendence.py)
-- This version of the table is updated for the timetable feature.
CREATE TABLE IF NOT EXISTS records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identity VARCHAR(255) NOT NULL,
    similarity VARCHAR(255),
    date DATE NOT NULL,
    time TIME NOT NULL,
    subject_name VARCHAR(255), -- Added for the timetable feature
    semester INT,              -- Added for the timetable feature
    CONSTRAINT fk_user_photo FOREIGN KEY (identity) REFERENCES users(photo_path) ON DELETE CASCADE
);

-- New timetable table for the Automatic Timetable Integration feature
-- This table stores the class schedule.
CREATE TABLE IF NOT EXISTS timetable (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    subject_name VARCHAR(255) NOT NULL,
    faculty_name VARCHAR(255) NOT NULL,
    semester INT NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL
);

-- Insert sample data into the timetable
-- You can modify this with your actual class schedule.
INSERT INTO timetable (course_name, subject_name, faculty_name, semester, day_of_week, start_time, end_time) VALUES
('BCA', 'Python Programming', 'Dr. Smith', 5, 'Monday', '09:00:00', '10:00:00'),
('BCA', 'Database Management', 'Prof. Jones', 5, 'Monday', '10:00:00', '11:00:00'),
('BCA', 'Software Engineering', 'Dr. Williams', 5, 'Tuesday', '11:00:00', '12:00:00');