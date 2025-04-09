CREATE DATABASE IF NOT EXISTS billing;

USE billing;

-- Drop and recreate the table if you're resetting
DROP TABLE IF EXISTS payment;

CREATE TABLE IF NOT EXISTS payment (
    paymentID INT AUTO_INCREMENT PRIMARY KEY,
    prescriptionID INT NOT NULL,
    patientID INT NOT NULL,
    patientEmail VARCHAR(120) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    stripeSessionID VARCHAR(255), 
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert Sample Data (optional)
INSERT INTO payment (prescriptionID, patientID, patientEmail, amount, status, stripeSessionID) VALUES
(101, 1, 'john@example.com', 50.00, 'completed', NULL),
(102, 2, 'jane@example.com', 75.50, 'pending', NULL),
(103, 3, 'lee@example.com', 20.00, 'completed', NULL),
(104, 1, 'john@example.com', 120.75, 'failed', NULL),
(105, 2, 'jane@example.com', 95.25, 'completed', NULL),
(106, 3, 'lee@example.com', 45.00, 'pending', NULL);


