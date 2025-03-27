-- Create the database
CREATE DATABASE IF NOT EXISTS appointmentdb;

-- Switch to the created database
USE appointmentdb;

-- Create the appointment table
CREATE TABLE IF NOT EXISTS appointment (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    appointment_status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_patient 
        FOREIGN KEY (patient_id) 
        REFERENCES patientdb.patient(id),
    CONSTRAINT fk_doctor 
        FOREIGN KEY (doctor_id) 
        REFERENCES doctors(doctor_id)
);
-- doctor fk has not been set up yet 

-- Add additional tables for 'patients' and 'doctors' to maintain foreign key constraints
-- Assuming these tables are needed, otherwise, you can skip them.

-- Create the patients table (for demonstration)
-- CREATE TABLE IF NOT EXISTS patients (
--     patient_id INT AUTO_INCREMENT PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     dob DATE,
--     phone VARCHAR(15)
-- );

-- Create the doctors table (for demonstration)
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    specialty VARCHAR(255),
    phone VARCHAR(15)
);

-- You may add indexes to improve performance
CREATE INDEX idx_appointment_doctor_id ON appointment (doctor_id);
CREATE INDEX idx_appointment_patient_id ON appointment (patient_id);
CREATE INDEX idx_appointment_date ON appointment (appointment_date);


-- Inserting some dummy data into doctors
INSERT INTO doctors (name, specialty, phone) VALUES
('Dr. John Doe', 'Cardiology', '1234567890'),
('Dr. Jane Smith', 'Pediatrics', '9876543210');

-- Inserting some dummy data into patients
-- INSERT INTO patients (name, dob, phone) VALUES
-- ('Alice Brown', '1990-05-15', '5551234567'),
-- ('Bob White', '1985-11-22', '5559876543');

INSERT INTO appointment (patient_id, doctor_id, appointment_date, start_time, end_time, appointment_status, notes) VALUES
(1, 1, '2024-04-15', '2024-04-15 10:00:00', '2024-04-15 11:00:00', 'Scheduled', 'Routine checkup'),
(2, 2, '2024-04-16', '2024-04-16 14:30:00', '2024-04-16 15:30:00', 'Scheduled', 'Follow-up consultation');