from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

# URLs for your atomic microservices
# patient_URL = "http://host.docker.internal:5001/patient"
# appointment_URL = "http://host.docker.internal:5002/appointment"
patient_URL = os.environ.get('PATIENT_SERVICE_URL')
appointment_URL = os.environ.get('APPOINTMENT_SERVICE_URL')

@app.route("/doctor_management", methods=["POST"])
def doctormanagement():
    """
    Composite endpoint that orchestrates a series of operations in sequence:

      1. Retrieve all appointments for a given doctor (key: "doctor_id") via
         GET {appointment_URL}/appointments/doctor/<doctor_id>.
         Enrich each appointment with patient details by calling the Patient service.
      2. Optionally, retrieve detailed information for a specific appointment (key: "appointment_details_id")
         via GET {appointment_URL}/appointments/<appointment_id>.
      3. Optionally, retrieve full patient records (key: "patient_id")
         via GET {patient_URL}/patient/<patient_id>.
      4. Optionally, update the appointment notes (diagnosis) (key: "update_notes").
         If provided, this key should be an object containing "appointment_id" (optional; if not provided, defaults to the first appointment) and "notes".
         Calls PATCH {appointment_URL}/appointments/<appointment_id>/notes.
      5. Optionally, update the appointment status (key: "update_status").
         If provided, this key should be an object containing "appointment_id" (optional) and "status".
         Calls PATCH {appointment_URL}/appointments/<appointment_id>/status.
         
    The endpoint aggregates and returns the results from each operation.
    """
    try:
        data = request.get_json()
        results = {}

        # --- Operation 1: Get all appointments for the doctor ---
        if "doctor_id" not in data:
            return jsonify({
                "code": 400,
                "message": "Missing required field: doctor_id"
            }), 400
        doctor_id = data["doctor_id"]
        url1 = f"{appointment_URL}/appointments/doctor/{doctor_id}"
        res1 = invoke_http(url1, method="GET")
        results["get_doctor_appointments"] = {
            "return_code": res1.get("code"),
            "response": res1
        }
        if res1.get("code") not in range(200, 300):
            return jsonify({
                "code": res1.get("code", 500),
                "message": f"Failed to retrieve appointments for doctor {doctor_id}.",
                "data": results
            }), res1.get("code", 500)
        appointments = res1.get("data", {}).get("appointments", [])
        if not appointments:
            return jsonify({
                "code": 404,
                "message": f"No appointments found for doctor {doctor_id}.",
                "data": results
            }), 404
        # Enrich each appointment with patient details.
        for appointment in appointments:
            pid = appointment.get("patient_id")
            if pid:
                patient_url = f"{patient_URL}/patient/{pid}"
                pres = invoke_http(patient_url, method="GET")
                if pres.get("code") in range(200, 300):
                    appointment["patient_details"] = pres.get("data")
                else:
                    appointment["patient_details"] = {"error": "Patient details not found"}
        results["get_doctor_appointments"]["enriched_appointments"] = appointments

        # Set default values from the first appointment for use in subsequent operations.
        default_app_id = appointments[0].get("appointment_id")
        default_patient_id = appointments[0].get("patient_id")

        # --- Operation 2: Get specific appointment details ---
        if "appointment_details_id" in data:
            app_id = data["appointment_details_id"]
        else:
            app_id = default_app_id  # use default if not provided
        url2 = f"{appointment_URL}/appointments/{app_id}"
        res2 = invoke_http(url2, method="GET")
        results["get_appointment_details"] = {
            "return_code": res2.get("code"),
            "response": res2
        }

        # --- Operation 3: Get patient records ---
        if "patient_id" in data:
            patient_id = data["patient_id"]
        else:
            patient_id = default_patient_id
        url3 = f"{patient_URL}/patient/{patient_id}"
        res3 = invoke_http(url3, method="GET")
        results["get_patient_records"] = {
            "return_code": res3.get("code"),
            "response": res3
        }

        # --- Operation 4: Update appointment notes (diagnosis) ---
        if "update_notes" in data:
            update_info = data["update_notes"]
            # Use the provided appointment_id if available, otherwise default.
            update_app_id = update_info.get("appointment_id", default_app_id)
            if "notes" in update_info:
                url4 = f"{appointment_URL}/appointments/{update_app_id}/notes"
                payload = {"notes": update_info["notes"]}
                res4 = invoke_http(url4, method="PATCH", json=payload)
                results["update_appointment_notes"] = {
                    "return_code": res4.get("code"),
                    "response": res4
                }
            else:
                results["update_appointment_notes"] = {
                    "return_code": 400,
                    "response": {"message": "Missing 'notes' in update_notes"}
                }
        else:
            results["update_appointment_notes"] = {
                "return_code": None,
                "response": "Not requested"
            }

        return jsonify({
            "code": 200,
            "message": "Composite orchestration completed.",
            "data": results
        }), 200

    except Exception as e:
        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        error_msg = f"{str(e)} at {str(exc_type)} in {fname} on line {exc_tb.tb_lineno}"
        return jsonify({
            "code": 500,
            "message": "Internal error in composite orchestration: " + error_msg
        }), 500

# Run the Flask app
if __name__ == "__main__":
    print("Doctor Management Composite Microservice is running...")
    app.run(host="0.0.0.0", port=6002, debug=True)