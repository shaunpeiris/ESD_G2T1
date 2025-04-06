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
(2, 'D002', '2025-04-04', '2025-04-04 10:00:00', '2025-04-04 10:30:00', 'Scheduled', 'Follow-up consultation'),
(1, 'D001', '2025-04-04', '2025-04-04 09:00:00', '2025-04-04 09:30:00', 'Scheduled', 'Routine checkup'),
(3, 'D003', '2025-04-04', '2025-04-04 11:00:00', '2025-04-04 11:30:00', 'Scheduled', 'New patient consultation'),
(1, 'D001', '2025-04-05', '2025-04-05 09:00:00', '2025-04-05 09:30:00', 'Scheduled', 'Routine checkup'),
(2, 'D002', '2025-04-05', '2025-04-05 10:00:00', '2025-04-05 10:30:00', 'Scheduled', 'Follow-up consultation'),
(3, 'D003', '2025-04-05', '2025-04-05 11:00:00', '2025-04-05 11:30:00', 'Scheduled', 'New patient consultation'),
(3, 'D001', '2025-04-05', '2025-04-05 11:00:00', '2025-04-05 11:30:00', 'Scheduled', 'New patient consultation'),
(4, 'D001', '2025-04-05', '2025-04-05 12:00:00', '2025-04-05 12:30:00', 'Scheduled', 'Follow-up consultation'),
(6, 'D001', '2025-04-05', '2025-04-05 12:30:00', '2025-04-05 13:00:00', 'Scheduled', 'New patient consultation'),
(1, 'D001', '2025-04-06', '2025-04-06 09:00:00', '2025-04-06 09:30:00', 'Scheduled', 'Routine checkup'),
(2, 'D002', '2025-04-06', '2025-04-06 10:00:00', '2025-04-06 10:30:00', 'Scheduled', 'Follow-up consultation'),
(3, 'D003', '2025-04-06', '2025-04-06 11:00:00', '2025-04-06 11:30:00', 'Scheduled', 'New patient consultation'),
(3, 'D001', '2025-04-06', '2025-04-06 11:00:00', '2025-04-06 11:30:00', 'Scheduled', 'New patient consultation'),
(4, 'D001', '2025-04-06', '2025-04-06 12:00:00', '2025-04-06 12:30:00', 'Scheduled', 'Follow-up consultation'),
(6, 'D001', '2025-04-06', '2025-04-06 12:30:00', '2025-04-06 13:00:00', 'Scheduled', 'New patient consultation'),
(1, 'D001', '2025-04-07', '2025-04-07 09:00:00', '2025-04-07 09:30:00', 'Scheduled', 'Routine checkup'),
(2, 'D002', '2025-04-07', '2025-04-07 10:00:00', '2025-04-07 10:30:00', 'Scheduled', 'Follow-up consultation'),
(3, 'D003', '2025-04-07', '2025-04-07 11:00:00', '2025-04-07 11:30:00', 'Scheduled', 'New patient consultation'),
(3, 'D001', '2025-04-08', '2025-04-08 11:00:00', '2025-04-08 11:30:00', 'Scheduled', 'New patient consultation'),
(4, 'D001', '2025-04-08', '2025-04-08 12:00:00', '2025-04-08 12:30:00', 'Scheduled', 'Follow-up consultation'),
(6, 'D001', '2025-04-08', '2025-04-08 12:30:00', '2025-04-08 13:00:00', 'Scheduled', 'New patient consultation'),
(1, 'D001', '2025-04-08', '2025-04-08 09:00:00', '2025-04-08 09:30:00', 'Scheduled', 'Routine checkup'),
(2, 'D001', '2025-04-08', '2025-04-08 10:00:00', '2025-04-08 10:30:00', 'Scheduled', 'Follow-up consultation'),
(3, 'D001', '2025-04-08', '2025-04-08 11:00:00', '2025-04-08 11:30:00', 'Scheduled', 'New patient consultation'),
(1, 'D001', '2025-04-09', '2025-04-09 09:00:00', '2025-04-09 09:30:00', 'Scheduled', 'Routine checkup'),
(2, 'D002', '2025-04-09', '2025-04-09 10:00:00', '2025-04-09 10:30:00', 'Scheduled', 'Follow-up consultation'),
(3, 'D003', '2025-04-09', '2025-04-09 11:00:00', '2025-04-09 11:30:00', 'Scheduled', 'New patient consultation'),
(9, 'D001', '2025-04-09', '2025-04-09 11:00:00', '2025-04-09 11:30:00', 'Scheduled', 'New patient consultation'),
(4, 'D001', '2025-04-09', '2025-04-09 12:00:00', '2025-04-09 12:30:00', 'Scheduled', 'Follow-up consultation'),
(6, 'D001', '2025-04-09', '2025-04-09 12:30:00', '2025-04-09 13:00:00', 'Scheduled', 'New patient consultation'),
(1, 'D001', '2025-04-10', '2025-04-10 09:00:00', '2025-04-10 09:30:00', 'Scheduled', 'Routine checkup'),
(2, 'D002', '2025-04-10', '2025-04-10 10:00:00', '2025-04-10 10:30:00', 'Scheduled', 'Follow-up consultation'),
(3, 'D003', '2025-04-10', '2025-04-10 11:00:00', '2025-04-10 11:30:00', 'Scheduled', 'New patient consultation'),
(4, 'D001', '2025-04-10', '2025-04-10 12:00:00', '2025-04-10 12:30:00', 'Scheduled', 'Follow-up consultation'),
(6, 'D001', '2025-04-10', '2025-04-10 12:30:00', '2025-04-10 13:00:00', 'Scheduled', 'New patient consultation'),
(7, 'D001', '2025-04-10', '2025-04-10 13:00:00', '2025-04-10 13:30:00', 'Scheduled', 'Routine checkup'),
(9, 'D001', '2025-04-10', '2025-04-10 11:00:00', '2025-04-10 11:30:00', 'Scheduled', 'New patient consultation'),
(10, 'D001', '2025-04-10', '2025-04-10 15:00:00', '2025-04-10 15:30:00', 'Scheduled', 'Follow-up consultation'),
(7, 'D001', '2025-04-10', '2025-04-10 16:30:00', '2025-04-10 16:00:00', 'Scheduled', 'New patient consultation'),
(1, 'D001', '2025-04-11', '2025-04-11 09:00:00', '2025-04-11 09:30:00', 'Scheduled', 'Routine checkup'),
(2, 'D002', '2025-04-11', '2025-04-11 10:00:00', '2025-04-11 10:30:00', 'Scheduled', 'Follow-up consultation'),
(3, 'D003', '2025-04-11', '2025-04-11 11:00:00', '2025-04-11 11:30:00', 'Scheduled', 'New patient consultation');