CREATE DATABASE IF NOT EXISTS billing;
USE billing;

-- Create the Payment Table
CREATE TABLE IF NOT EXISTS payment (
    paymentID INT AUTO_INCREMENT PRIMARY KEY,
    prescriptionID INT NOT NULL,
    patientID INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert Fake Data
INSERT INTO payment (prescriptionID, patientID, amount, status) VALUES
(101, 1, 50.00, 'completed'),
(102, 2, 75.50, 'pending'),
(103, 3, 20.00, 'completed'),
(104, 1, 120.75, 'failed'),
(105, 2, 95.25, 'completed'),
(106, 3, 45.00, 'pending');
