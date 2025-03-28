from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
import os

app = Flask(__name__)
CORS(app)

# Use the prescription database (make sure the 'prescription.sql' file is executed beforehand)
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
#     "dbURL",
#     "mysql+mysqlconnector://root@localhost:3306/prescriptiondb"  # Updated to prescriptiondb
# )

db_uri = environ.get('dbURL') 
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Prescription(db.Model):
    __tablename__ = 'prescription'  # Updated to lowercase to match database
    prescription_id = db.Column('prescriptionID', db.Integer, primary_key=True, autoincrement=True)  # Updated to match column name
    medicine = db.Column('medicine', db.JSON, nullable=False)
    appointment_id = db.Column('appointmentID', db.Integer, nullable=False)  # Updated to match column name
    status = db.Column('status', db.Boolean, default=False)  # Added status field
    
    def json(self):
        return {
            "prescription_id": self.prescription_id,
            "medicine": self.medicine,
            "appointment_id": self.appointment_id,
            "status": self.status  # Added status to JSON response
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
    status = request.json.get('status', False)  # Default to False if not provided
    
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
        prescription.status = status  # Update status if provided
        message = "Prescription updated"
    else:
        # Create new prescription
        prescription = Prescription(
            appointment_id=appointment_id, 
            medicine=medicine,
            status=status  # Set status on creation
        )
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

# Add a new endpoint to update prescription status
@app.route("/prescription/<int:prescription_id>/status", methods=['PUT'])
def update_prescription_status(prescription_id):
    """
    This endpoint allows updating the status of a prescription.
    It expects a JSON payload with:
      - status: Boolean value indicating the new status
    """
    prescription = Prescription.query.get(prescription_id)
    
    if not prescription:
        return jsonify({
            "code": 404,
            "message": f"Prescription not found for id {prescription_id}"
        }), 404
    
    status = request.json.get('status')
    if status is None:
        return jsonify({
            "code": 400,
            "message": "Missing status information."
        }), 400
    
    prescription.status = status
    
    try:
        db.session.commit()
        return jsonify({
            "code": 200,
            "message": "Prescription status updated",
            "data": prescription.json()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred: " + str(e)
        }), 500

if __name__ == '__main__':
    print("Prescription Microservice is running on " + os.path.basename(__file__))
    app.run(host='0.0.0.0', port=5003, debug=True)
