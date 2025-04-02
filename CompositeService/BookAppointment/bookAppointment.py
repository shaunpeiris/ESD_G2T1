from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DOCTOR_API_URL = "http://104.214.186.4:5010/doctors"
AVAILABILITY_API_URL = "http://104.214.186.4:5000/doctor_availabilities"
APPOINTMENT_API_URL = "http://appointment:5002/appointment"
PATIENT_API_URL = "http://patient:5001/patient"
NOTIFICATION_API_URL = "http://notification:5005"

# 🔔 Notification helpers
def send_sms(to_phone, message):
    payload = {
        "method": "sms",
        "recipient": to_phone,
        "message": message
    }
    response = requests.post(f"{NOTIFICATION_API_URL}/notify", json=payload)
    return response.json()

def send_email(to_email, subject, message):
    payload = {
        "method": "email",
        "recipient": to_email,
        "subject": subject,
        "message": message
    }
    response = requests.post(f"{NOTIFICATION_API_URL}/notify", json=payload)
    return response.json()

@app.route("/searchDoctors")
def search_available_doctors():
    specialization = request.args.get("specialization", "Any")
    polyclinic = request.args.get("polyclinic", "Any")
    date = request.args.get("date")

    if not date:
        return jsonify({"success": False, "message": "Missing required 'date' parameter"}), 400

    try:
        doc_res = requests.get(DOCTOR_API_URL)
        doc_data = doc_res.json()
        doctors = doc_data.get("data", [])

        filtered_doctors = [d for d in doctors if
            (specialization == "Any" or d["Specialization"] == specialization) and
            (polyclinic == "Any" or d["Polyclinic"] == polyclinic)
        ]

        avail_res = requests.get(f"{AVAILABILITY_API_URL}?date={date}")
        avail_data = avail_res.json()
        availabilities = avail_data.get("data", [])

        available_map = {}
        for a in availabilities:
            if a.get("Available") is True:
                doctor_id = a["DoctorID"]
                available_map.setdefault(doctor_id, []).append(a["StartTime"])

        result = []
        for doc in filtered_doctors:
            doc_id = doc["Doctor_ID"]
            times = available_map.get(doc_id, [])
            if times:
                result.append({
                    "Doctor_ID": doc_id,
                    "Doctor_Name": doc["Doctor_Name"],
                    "Specialization": doc["Specialization"],
                    "Polyclinic": doc["Polyclinic"],
                    "timeslots": sorted(times)
                })

        return jsonify({"success": True, "data": result})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error fetching doctors or availability: {str(e)}"}), 500

@app.route("/createAppointment", methods=['POST'])
def create_appointment():
    try:
        patient_id = 12  # Example static value
        if not patient_id:
            return jsonify({"success": False, "message": "Missing Patient ID"}), 401

        patient_res = requests.get(f"{PATIENT_API_URL}/{patient_id}")
        if patient_res.status_code != 200:
            return jsonify({"success": False, "message": "Patient not found"}), 404

        patient_data = patient_res.json().get("data", {})
        patient_phone = patient_data.get("mobile")
        patient_email = patient_data.get("email")

        if not patient_phone or not patient_email:
            return jsonify({"success": False, "message": "Patient phone or email is missing"}), 400

        payload = request.get_json()
        required_fields = ["doctor_id", "doctor_name", "appointment_date", "start_time", "end_time"]
        if not all(field in payload for field in required_fields):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        doctor_id = payload["doctor_id"]
        doctor_name = payload["doctor_name"]
        appointment_date = payload["appointment_date"]
        start_time = payload["start_time"]
        payload["appointment_status"] = "Assigned"
        end_time = payload["end_time"]

        response = requests.post(APPOINTMENT_API_URL, json=payload)
        appointment_result = response.json()

        if response.status_code != 201:
            return jsonify({"success": False, "message": "Failed to create appointment", "details": appointment_result}), response.status_code

        try:
            time_only = start_time.split("T")[1] if "T" in start_time else start_time

            availability_payload = {
                "DoctorID": doctor_id,
                "Date": appointment_date,
                "StartTime": time_only,
                "Available": False
            }

            avail_res = requests.post(f"{AVAILABILITY_API_URL}/update", json=availability_payload)
            if not avail_res.ok:
                return jsonify({
                    "success": False,
                    "message": "Appointment created but failed to update availability",
                    "availability_response": avail_res.text
                }), 500
        except Exception as avail_error:
            return jsonify({
                "success": False,
                "message": f"Appointment created but failed to update availability: {str(avail_error)}"
            }), 500

        message = f"Your appointment with Dr. {doctor_name} is confirmed for {appointment_date} at {start_time}."
        subject = "Appointment Confirmation"

        try:
            sms_result = send_sms(patient_phone, message)
            email_result = send_email(patient_email, subject, message)
        except Exception as notify_error:
            return jsonify({
                "success": False,
                "message": f"Appointment created but notification failed: {str(notify_error)}"
            }), 500

        return jsonify({
            "success": True,
            "message": "Appointment successfully created",
            "appointment": appointment_result
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

