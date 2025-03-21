from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from os import environ # need to add to our environment variables later
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/patientdb'
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Patient(db.Model):
    __tablename__ = 'patient'

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    medicalHistory = db.Column(db.JSON, nullable=True)

    def __init__(self, id, name, email, password, medicalHistory):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.medicalHistory = medicalHistory

    def json(self):
        return {"id": self.id, "name": self.name, "email": self.email, "password": self.password, "medicalHistory": self.medicalHistory}

@app.route("/patient")
def get_all():
    patient_list = db.session.scalars(db.select(Patient)).all()

    if len(patient_list):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "patients": [patient.json() for patient in patient_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no patients."
        }
    ), 404


@app.route("/patient/<int:id>")
def get_patient_by_id(id):
    patient = db.session.scalars(
    	db.select(Patient).filter_by(id=int(id)).
    	limit(1)
    ).first()

    if patient:
        return jsonify(
            {
                "code": 200,
                "data": patient.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Patient not found."
        }
    ), 404

# Replace the existing update_medical_history function with this improved version

@app.route("/patient/update", methods=['PUT'])
def update_medical_history():
    """Update a patient's medical history including allergies, medical conditions, etc."""
    data = request.get_json()
    id = data["id"]
    new_medical_history = data["medicalHistory"]

    patient = db.session.scalars(
        db.select(Patient).filter_by(id=int(id)).
        limit(1)
    ).first()

    if not patient:
        return jsonify(
            {
                "code": 404,
                "message": "Patient not found."
            }
        ), 404

    # Initialize empty medical history if none exists
    if patient.medicalHistory is None:
        patient.medicalHistory = {
            "allergies": [],
            "medical_conditions": [],
            "past_surgeries": [],
            "family_medical_history": [],
            "chronic_illnesses": [],
            "medications": []
        }
    
    # Define the categories we expect to update
    categories = [
        "allergies", 
        "medical_conditions", 
        "past_surgeries", 
        "family_medical_history", 
        "chronic_illnesses", 
        "medications"
    ]
    
    # Update medical history with new data for each category
    for category in categories:
        if category in new_medical_history:
            # Make sure all values are strings if they're not arrays
            if new_medical_history[category] and not isinstance(new_medical_history[category], list):
                patient.medicalHistory[category] = [str(new_medical_history[category])]
            else:
                patient.medicalHistory[category] = new_medical_history[category]

    try:
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "data": patient.json()
            }
        ), 200
    except Exception as e:
        print(f"Error updating medical history: {str(e)}")
        return jsonify(
            {
                "code": 500,
                "data": data,
                "message": "An error occurred updating the patient's medical history."
            }
        ), 500

@app.route("/patient/login", methods=['POST'])
def login():

    data = request.get_json()
    email = data["email"]
    password = data["password"]

    patient = db.session.scalars(
    	db.select(Patient).filter_by(email=email, password=password)
    ).first()

    if patient:
        return jsonify(
            {
                "code": 200,
                "data": patient.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Incorrect email or password."
        }
    ), 404

@app.route("/patient/update/personal", methods=['PUT'])
def update_personal_info():
    """Update a patient's personal information (name and email)"""
    data = request.get_json()
    id = data["id"]
    new_name = data.get("name")
    new_email = data.get("email")

    patient = db.session.scalars(
        db.select(Patient).filter_by(id=int(id)).
        limit(1)
    ).first()

    if not patient:
        return jsonify(
            {
                "code": 404,
                "message": "Patient not found."
            }
        ), 404

    # Update the patient information if provided
    if new_name:
        patient.name = new_name
    if new_email:
        patient.email = new_email

    try:
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": data,
                "message": "An error occurred updating the patient's personal information."
            }
        ), 500

    return jsonify(
        {
            "code": 200,
            "data": patient.json()
        }
    ), 200

@app.route("/patient/update/password", methods=['PUT'])
def update_password():
    """Update a patient's password"""
    data = request.get_json()
    id = data["id"]
    current_password = data["currentPassword"]
    new_password = data["newPassword"]

    patient = db.session.scalars(
        db.select(Patient).filter_by(id=int(id)).
        limit(1)
    ).first()

    if not patient:
        return jsonify(
            {
                "code": 404,
                "message": "Patient not found."
            }
        ), 404

    # Verify the current password
    if patient.password != current_password:
        return jsonify(
            {
                "code": 401,
                "message": "Current password is incorrect."
            }
        ), 401

    # Update the password
    patient.password = new_password

    try:
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {"id": id},
                "message": "An error occurred updating the password."
            }
        ), 500

    return jsonify(
        {
            "code": 200,
            "message": "Password updated successfully.",
            "data": patient.json()
        }
    ), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)