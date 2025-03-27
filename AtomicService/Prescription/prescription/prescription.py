from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
import os

app = Flask(__name__)
CORS(app)

# Use the prescription database (make sure the 'prescription.sql' file is executed beforehand)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "dbURL",
    "mysql+mysqlconnector://root@localhost:3306/prescription"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Prescription(db.Model):
    __tablename__ = 'Prescription'
    prescription_id = db.Column('PrescriptionID', db.Integer, primary_key=True, autoincrement=True)
    medicine = db.Column('Medicine', db.JSON, nullable=False)
    appointment_id = db.Column('AppointmentID', db.Integer, nullable=False)
    
    def json(self):
        return {
            "prescription_id": self.prescription_id,
            "medicine": self.medicine,
            "appointment_id": self.appointment_id
        }

@app.route("/prescription", methods=['POST'])
def create_or_update_prescription():
    """
    This endpoint is used by the "Create Prescription" Composite microservice.
    It expects a JSON payload with:
      - appointment_id: The ID associated with the appointment.
      - medicine: A JSON object/array containing the medicine details.
    
    It will either create a new prescription or update an existing one for the given appointment ID,
    then return the updated prescription.
    """
    appointment_id = request.json.get('appointment_id')
    medicine = request.json.get('medicine')
    
    if not appointment_id or not medicine:
        return jsonify({
            "code": 400,
            "message": "Missing appointment_id or medicine information."
        }), 400

    # Check if a prescription already exists for the given appointment ID
    prescription = Prescription.query.filter_by(appointment_id=appointment_id).first()
    
    if prescription:
        # Update existing prescription
        prescription.medicine = medicine
        message = "Prescription updated"
    else:
        # Create new prescription
        prescription = Prescription(appointment_id=appointment_id, medicine=medicine)
        db.session.add(prescription)
        message = "Prescription created"
    
    try:
        db.session.commit()
        return jsonify({
            "code": 200,
            "message": message,
            "data": prescription.json()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred: " + str(e)
        }), 500

@app.route("/prescription/<int:prescription_id>", methods=['GET'])
def get_prescription(prescription_id):
    """
    This endpoint is used by the "Pharmacy Service" Composite microservice.
    It retrieves the prescription details based on the Prescription ID.
    """
    prescription = Prescription.query.get(prescription_id)
    
    if prescription:
        return jsonify({
            "code": 200,
            "data": prescription.json()
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": f"Prescription not found for id {prescription_id}"
        }), 404

if __name__ == '__main__':
    print("Prescription Microservice is running on " + os.path.basename(__file__))
    app.run(host='0.0.0.0', port=5000, debug=True)
