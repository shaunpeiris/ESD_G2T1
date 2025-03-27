-- Create the database
CREATE DATABASE IF NOT EXISTS appointmentdb;

-- Switch to the created database
USE appointmentdb;

-- Create the appointment table
CREATE TABLE IF NOT EXISTS appointment (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id VARCHAR(4) NOT NULL,
    appointment_date DATE NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    appointment_status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- indexes to improve performance
CREATE INDEX idx_appointment_doctor_id ON appointment (doctor_id);
CREATE INDEX idx_appointment_patient_id ON appointment (patient_id);
CREATE INDEX idx_appointment_date ON appointment (appointment_date);

INSERT INTO appointment (patient_id, doctor_id, appointment_date, start_time, end_time, appointment_status, notes) VALUES
(1, 'D001', '2024-04-15', '2024-04-15 10:00:00', '2024-04-15 11:00:00', 'Scheduled', 'Routine checkup'),
(2, 'D002', '2024-04-16', '2024-04-16 14:30:00', '2024-04-16 15:30:00', 'Scheduled', 'Follow-up consultation');