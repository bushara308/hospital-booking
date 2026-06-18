-- Database Schema for Hospital Appointment Booking System
-- Create Database
CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- 1. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Doctors Table
CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    available_days VARCHAR(100) DEFAULT 'Mon-Fri'
);

-- 3. Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- 4. Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected', 'Cancelled') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- Insert Sample Data
-- Sample Doctors
INSERT INTO doctors (name, specialization, phone) VALUES 
('Dr. Amar Rasal', 'Cardiologist', '1234567890'),
('Dr. Vishal Mutkule', 'Dermatologist', '0987654321'),
('Dr. Imran Khan', 'Pediatrician', '1122334455'),
('Dr. Suvarna Karpe', 'Neurologist', '5566778899');

-- Sample Admin (password is 'admin123' hashed using pbkdf2:sha256)
-- We will generate this in Python, but for now we put a placeholder.
-- This hash represents 'admin123'. 
INSERT INTO admins (username, password_hash) VALUES 
('admin', 'scrypt:32768:8:1$N2B3a7jA0J0yCZyP$0f488663806201b22db95c62dfca4c759cd5a4a58b6680a65bb51a5d625d911b3be05de901bbd3c52e461b2fb8d1ebcd25e0a6d07e60b1e42dd667b9d620ca6e');

-- Sample Patients
-- Password for these patients is 'password123'
INSERT INTO patients (name, email, password_hash, phone) VALUES 
('John Doe', 'john@example.com', 'scrypt:32768:8:1$uH3A4TbxVq6A5s4A$f639014167e435cfd137b018b108cbac297b77abdc2f201e66cff7f16f1a8c081e649e49eb72d2fb741362096bb759187a50fc49bbfe117a356073ea61407e3a', '5551234567'),
('Jane Roe', 'jane@example.com', 'scrypt:32768:8:1$uH3A4TbxVq6A5s4A$f639014167e435cfd137b018b108cbac297b77abdc2f201e66cff7f16f1a8c081e649e49eb72d2fb741362096bb759187a50fc49bbfe117a356073ea61407e3a', '5559876543');

-- Sample Appointments
INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status) VALUES 
(1, 1, '2024-06-15', '10:00:00', 'Approved'),
(1, 2, '2024-06-20', '14:30:00', 'Pending'),
(2, 3, '2024-06-18', '09:15:00', 'Pending');
show tables;
