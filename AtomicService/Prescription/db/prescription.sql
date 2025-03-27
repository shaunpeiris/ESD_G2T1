 -- Uncomment the following lines to drop the table if it exists and create a new one:
CREATE DATABASE IF NOT EXISTS prescriptiondb;

USE prescriptiondb;

CREATE TABLE IF NOT EXISTS prescription (
        prescriptionID INT PRIMARY KEY AUTO_INCREMENT,
        medicine JSON NOT NULL,
        appointmentID INT,
        status BOOLEAN DEFAULT FALSE
        -- ,FOREIGN KEY (AppointmentID) REFERENCES Appointment(AppointmentID)
    );
    
    -- Insert sample data into Prescription table
    INSERT INTO prescription (medicine, appointmentID)
    VALUES 
      ('{"medications": [{"name": "Paracetamol", "dose": "500mg", "frequency": "twice a day"}]}', 1),
      ('{"medications": [{"name": "Ibuprofen", "dose": "200mg", "frequency": "three times a day"}]}', 2),
      ('{"medications": [{"name": "Amoxicillin", "dose": "250mg", "frequency": "three times a day"}]}', 3),
      ('{"medications": [{"name": "Ciprofloxacin", "dose": "500mg", "frequency": "once a day"}]}', 4),
      ('{"medications": [{"name": "Metformin", "dose": "850mg", "frequency": "twice a day"}]}', 5),
      ('{"medications": [{"name": "Aspirin", "dose": "81mg", "frequency": "once a day"}]}', 6);
    
