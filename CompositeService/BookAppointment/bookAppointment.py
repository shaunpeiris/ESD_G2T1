from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DOCTOR_API_URL = "http://104.214.186.4:5010/doctors"
AVAILABILITY_API_URL = "http://104.214.186.4:5000/doctor_availabilities"
APPOINTMENT_API_URL = "http://appointment:5002/appointment"
PATIENT_API_URL = "http://patient:5001/patient"
NOTIFICATION_API_URL = "http://notification:5015/notify"

@app.route("/searchDoctors")
def search_available_doctors():
    specialization = request.args.get("specialization", "Any")
    polyclinic = request.args.get("polyclinic", "Any")
    date = request.args.get("date")

    if not date:
        return jsonify({"success": False, "message": "Missing required 'date' parameter"}), 400

    try:
        # Step 1: Fetch doctors
        doc_res = requests.get(DOCTOR_API_URL)
        doc_data = doc_res.json()
        doctors = doc_data.get("data", [])

        # Filter doctors by specialization and polyclinic
        filtered_doctors = [d for d in doctors if
            (specialization == "Any" or d["Specialization"] == specialization) and
            (polyclinic == "Any" or d["Polyclinic"] == polyclinic)
        ]

        # Step 2: Fetch availability for selected date
        avail_res = requests.get(f"{AVAILABILITY_API_URL}?date={date}")
        avail_data = avail_res.json()
        availabilities = avail_data.get("data", [])

        # Step 3: Only include timeslots where Available == true
        available_map = {}
        for a in availabilities:
            if a.get("Available") is True:
                doctor_id = a["DoctorID"]
                available_map.setdefault(doctor_id, []).append(a["StartTime"])

        # Step 4: Merge doctor info with available times
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

        return jsonify({"data": result})

    except Exception as e:
        print("❌ Error in composite service:", e)
        return jsonify({"success": False, "message": "Failed to fetch or process data"}), 500

@app.route("/createAppointment", methods=['POST'])
def create_appointment():
    try:
        # 🔹 Step 1: Get Patient ID (Assuming it's passed in headers or session)
        patient_id = 12  # Example, replace with dynamic patient_id if needed
        if not patient_id:
            return jsonify({"success": False, "message": "Missing Patient ID"}), 401

        # 🔹 Step 2: Retrieve Patient Information
        patient_res = requests.get(f"{PATIENT_API_URL}/{patient_id}")
        if patient_res.status_code != 200:
            return jsonify({"success": False, "message": "Patient not found"}), 404

        patient_data = patient_res.json().get("data", {})
        patient_phone = patient_data.get("mobile")
        patient_email = patient_data.get("email")

        if not patient_phone or not patient_email:
            return jsonify({"success": False, "message": "Patient phone or email is missing"}), 400

        # 🔹 Step 3: Get Appointment Details from Request
        payload = request.get_json()
        required_fields = ["doctor_id", "doctor_name", "appointment_date", "start_time", "end_time"]
        if not all(field in payload for field in required_fields):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        doctor_id = payload["doctor_id"]
        appointment_date = payload["appointment_date"]
        start_time = payload["start_time"]
        end_time = payload["end_time"]

        # 🔹 Step 4: Create Appointment
        response = requests.post(APPOINTMENT_API_URL, json=payload)
        appointment_result = response.json()

        if response.status_code != 201:
            print(f"❌ Error creating appointment: {appointment_result}")
            return jsonify(appointment_result), response.status_code  # Forward error if appointment fails

        # 🔹 Step 5: Update Doctor Availability
        try:
            availability_payload = {
                "DoctorID": doctor_id,
                "Date": appointment_date,
                "StartTime": start_time.split("T")[1],  # Extracts the time
                "Available": False
            }
            avail_res = requests.post(f"{AVAILABILITY_API_URL}/update", json=availability_payload)
            if not avail_res.ok:
                raise Exception("Failed to update doctor availability")
        except Exception as avail_error:
            return jsonify({
                "code": 500,
                "message": f"Appointment created but failed to update availability: {str(avail_error)}"
            }), 500

        # 🔹 Step 6: Send Notifications (SMS & Email)
        notification_message = f"Your appointment with Dr. {payload['doctor_name']} is confirmed for {appointment_date} at {start_time}."
        notification_data = {
            "message": notification_message,
            "subject": "Appointment Confirmation"
        }

        try:
            # Send SMS
            sms_notification_data = {
                **notification_data,
                "recipient": patient_phone,
                "method": "sms"
            }
            sms_res = requests.post(NOTIFICATION_API_URL, json=sms_notification_data)
            print("SMS Response Status:", sms_res.status_code)
            print("SMS Response Text:", sms_res.text)

            # Send Email
            email_notification_data = {
                **notification_data,
                "recipient": patient_email,
                "method": "email"
            }
            email_res = requests.post(NOTIFICATION_API_URL, json=email_notification_data)
            print("Email Response Status:", email_res.status_code)
            print("Email Response Text:", email_res.text)

        except Exception as notify_error:
            print(f"⚠️ Notification failed: {str(notify_error)}")  

        # 🔹 Step 7: Return Success Response
        return jsonify({
            "success": True,
            "message": "Appointment successfully created",
            "appointment": appointment_result
        }), 201

    except Exception as e:
        print(f"❌ Error in create_appointment: {str(e)}")
        return jsonify({"code": 500, "message": f"Server error: {str(e)}"}), 500




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)