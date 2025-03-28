-- Drop and recreate the database
DROP DATABASE IF EXISTS prescriptiondb;
CREATE DATABASE prescriptiondb;
USE prescriptiondb;

-- Create the prescription table
CREATE TABLE IF NOT EXISTS prescription (
    prescriptionID INT PRIMARY KEY AUTO_INCREMENT,
    medicine JSON NOT NULL,
    appointmentID INT,
    status BOOLEAN DEFAULT FALSE
);

-- Insert sample data with status and quantity fields
INSERT INTO prescription (medicine, appointmentID, status)
VALUES 
    ('{"medications": [{"name": "Paracetamol", "dose": "500mg", "frequency": "twice a day", "quantity": 30}]}', 1, TRUE),
    ('{"medications": [{"name": "Ibuprofen", "dose": "200mg", "frequency": "three times a day", "quantity": 20}]}', 2, FALSE),
    ('{"medications": [{"name": "Amoxicillin", "dose": "250mg", "frequency": "three times a day", "quantity": 15}]}', 3, TRUE),
    ('{"medications": [{"name": "Ciprofloxacin", "dose": "500mg", "frequency": "once a day", "quantity": 10}]}', 4, FALSE),
    ('{"medications": [{"name": "Metformin", "dose": "850mg", "frequency": "twice a day", "quantity": 60}]}', 5, TRUE),
    ('{"medications": [{"name": "Aspirin", "dose": "81mg", "frequency": "once a day", "quantity": 90}]}', 6, FALSE);

-- Update existing records to modify status (optional, if needed)
UPDATE prescription SET 
    medicine = JSON_SET(medicine, '$.medications[0].quantity', 30),
    status = TRUE 
WHERE prescriptionID = 1;

UPDATE prescription SET 
    medicine = JSON_SET(medicine, '$.medications[0].quantity', 20),
    status = FALSE 
WHERE prescriptionID = 2;

UPDATE prescription SET 
    medicine = JSON_SET(medicine, '$.medications[0].quantity', 15),
    status = TRUE 
WHERE prescriptionID = 3;

UPDATE prescription SET 
    medicine = JSON_SET(medicine, '$.medications[0].quantity', 10),
    status = FALSE 
WHERE prescriptionID = 4;

UPDATE prescription SET 
    medicine = JSON_SET(medicine, '$.medications[0].quantity', 60),
    status = TRUE 
WHERE prescriptionID = 5;

UPDATE prescription SET 
    medicine = JSON_SET(medicine, '$.medications[0].quantity', 90),
    status = FALSE 
WHERE prescriptionID = 6;
