from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from os import environ # need to add to our environment variables later
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/patientdb'
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

# update medical history
@app.route("/patient/update", methods=['PUT'])
def update_medical_history():

    data = request.get_json()
    id = data["id"]
    new_medical_history = data["medicalHistory"]

    patient = db.session.scalars(
    	db.select(Patient).filter_by(id=int(id)).
    	limit(1)
    ).first()

    if patient.medicalHistory == None:
        existing_medical_history = {
            "allergies": [],
            "medical_conditions": [],
            "past_surgeries": [],
            "family_medical_history": [],
            "chronic_illnesses": [],
            "medications": []
        }
    else: 
        existing_medical_history = patient.medicalHistory

    # Update each category in the medical history
    for category in ["allergies", "medical_conditions", "past_surgeries", 
                     "family_medical_history", "chronic_illnesses", "medications"]:
        if category in new_medical_history:
            if category not in existing_medical_history:
                existing_medical_history[category] = []
            existing_medical_history[category].extend(new_medical_history[category])

    patient.medicalHistory = existing_medical_history

    try:
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": data,
                "message": "An error occurred updating the patient's medical history."
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": patient.json()
        }
    ), 201

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)