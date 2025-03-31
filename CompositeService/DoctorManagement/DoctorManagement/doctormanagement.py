from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

# URLs for your atomic microservices
patient_URL = "http://host.docker.internal:5001/patient"
appointment_URL = "http://host.docker.internal:5002/appointment"

@app.route("/doctor_management/appointments/doctor/<int:doctor_id>", methods=["GET"])
def get_doctor_appointments(doctor_id):
    """
    Retrieve all upcoming appointments for a given doctor and enrich each appointment with patient details.

    Steps:
      1. UI sends GET request with doctor_id.
      2. Composite service calls Appointment Atomic Service at /appointment/doctor/<doctor_id>.
      3. Retrieves a list of appointments.
      4. For each appointment, extract the patient_id and retrieve basic patient details.
      5. Return aggregated appointment data (with patient details) to the UI.
    """
    try:
        # Step 2: Invoke the Appointment Service
        appointment_result = invoke_http(
            f"{appointment_URL}/{doctor_id}",
            method='GET'
        )
        print("[Doctor Management] Appointment service response:", appointment_result)
        
        if appointment_result.get("code") not in range(200, 300):
            return jsonify({
                "code": 500,
                "message": "Failed to retrieve appointments for the doctor."
            }), 500
        
        # Assume appointment_result returns:
        # { "code": 200, "data": { "appointments": [ { ... }, { ... } ] } }
        appointments = appointment_result.get("data", {}).get("appointments", [])
        
        # Enrich each appointment with patient details
        for appointment in appointments:
            patient_id = appointment.get("patient_id")
            patient_result = invoke_http(
                f"{patient_URL}/{patient_id}",
                method='GET'
            )
            if patient_result.get("code") in range(200, 300):
                # Attach basic patient info (could be extended as needed)
                appointment["patient_details"] = patient_result.get("data")
            else:
                appointment["patient_details"] = {"error": "Patient details not found"}
        
        return jsonify({
            "code": 200,
            "data": {
                "doctor_id": doctor_id,
                "appointments": appointments
            }
        }), 200
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        ex_str = f"{str(e)} at {exc_type}: {fname}: line {str(exc_tb.tb_lineno)}"
        return jsonify({
            "code": 500,
            "message": "Internal error retrieving doctor's appointments: " + ex_str
        }), 500


@app.route("/doctor_management/patient_records/<int:patient_id>", methods=["GET"])
def get_patient_records(patient_id):
    """
    Retrieve a patient's full records (including medical history) based on patient id.

    Steps:
      5. UI: Doctor clicks on a patient from the upcoming list.
      6. Composite service calls the Patient Atomic Service at /patient/<patient_id>.
      7. Retrieve the patient's detailed records (e.g., medical history).
      8. Return the patient's records to the UI for display.
    """
    try:
        # Step 6: Invoke the Patient Service to retrieve patient records
        patient_result = invoke_http(
            f"{patient_URL}/{patient_id}",
            method="GET"
        )
        print("[Doctor Management] Patient service response:", patient_result)
        
        if patient_result.get("code") not in range(200, 300):
            return jsonify({
                "code": 500,
                "message": "Failed to retrieve patient records.",
                "data": patient_result
            }), 500
        
        # Step 8: Return the patient records to the UI
        return jsonify({
            "code": 200,
            "data": patient_result.get("data")
        }), 200
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        ex_str = f"{str(e)} at {str(exc_type)}: {fname}: line {str(exc_tb.tb_lineno)}"
        return jsonify({
            "code": 500,
            "message": "Internal error retrieving patient records: " + ex_str
        }), 500


# Run the Flask app
if __name__ == "__main__":
    print("Doctor Management Composite Microservice is running...")
    app.run(host="0.0.0.0", port=6002, debug=True)