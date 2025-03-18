-- Assuming the database doesn't exist
CREATE DATABASE IF NOT EXISTS patientdb;

USE patientdb; 

CREATE TABLE IF NOT EXISTS patient (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  medicalHistory JSON
);

INSERT INTO patient (name, email, password, medicalHistory)
VALUES 
  ('Emma Taylor', 'emma@example.com', 'pass123', 
    '{"allergies": ["Penicillin"], "medical_conditions": [], "past_surgeries": [], "family_medical_history": [], "chronic_illnesses": [], "medications": []}'),
  ('Noah Parker', 'noah@example.com', 'pass123', 
    '{"allergies": ["Peanuts", "Shellfish"], "medical_conditions": ["Asthma"], "past_surgeries": [], "family_medical_history": ["Diabetes"], "chronic_illnesses": [], "medications": ["Ventolin"]}'),
  ('Sophia Martinez','sophia@example.com','pass123', 
    '{"allergies": ["Latex", "Dairy"], "medical_conditions": [], "past_surgeries": ["Appendectomy"], "family_medical_history": [], "chronic_illnesses": [], "medications": []}'),
  ('Liam Rodriguez', 'liam@example.com', 'pass123', NULL),
  ('Olivia Thompson', 'olivia@example.com', 'pass123', NULL),
  ('Ethan Kim', 'ethan@example.com', 'pass123', NULL),
  ('Ava Singh', 'ava@example.com', 'pass123', 
    '{"allergies": ["Eggs", "Sulfa drugs"], "medical_conditions": ["Hypertension"], "past_surgeries": [], "family_medical_history": ["Heart disease"], "chronic_illnesses": ["Hypertension"], "medications": ["Lisinopril"]}'),
  ('Lucas Patel', 'lucas@example.com', 'pass123', 
    '{"allergies": ["Aspirin", "Ibuprofen"], "medical_conditions": ["Migraine"], "past_surgeries": [], "family_medical_history": [], "chronic_illnesses": ["Migraine"], "medications": ["Sumatriptan"]}'),
  ('Isabella Johnson', 'isabella@example.com', 'pass123', NULL),
  ('Mason Wilson', 'mason@example.com', 'pass123', NULL),
  ('Charlotte Brown', 'charlotte@example.com', 'pass123', 
    '{"allergies": ["Wheat"], "medical_conditions": ["Celiac Disease"], "past_surgeries": [], "family_medical_history": ["Autoimmune disorders"], "chronic_illnesses": ["Celiac Disease"], "medications": ["Vitamin supplements"]}');