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
def create_appointment_proxy():
    try:
        # Assuming you have the patient's ID stored in session after login
        # patient_id = session.get('patient_id')  # This assumes you've set 'patient_id' in the session during login

        patient_id = "1"
        
        if not patient_id:
            return jsonify({"success": False, "message": "Patient not logged in"}), 401
        
        payload = request.get_json()

        # Step 1: Get patient information by querying the Patient API
        patient_res = requests.get(f"{PATIENT_API_URL}/{patient_id}")
        # Log the status code and raw content to see what is being returned
        print("Patient API Response Code:", patient_res.status_code)
        print("Patient API Response Content:", patient_res.text)
        if patient_res.status_code != 200:
            return jsonify({"success": False, "message": "Patient not found"}), 404

        patient_data = patient_res.json()
        print("Patient Data:", patient_data)  # Log the response to check the data

        patient_phone = patient_data.get("mobile")
        patient_email = patient_data.get("data.email")

        if not patient_phone or not patient_email:
            return jsonify({"success": False, "message": "Patient phone or email is missing"}), 400


        # Step 2: Create the appointment via internal API
        response = requests.post(APPOINTMENT_API_URL, json=payload)
        appointment_result = response.json()
        
        # Step 3: If appointment succeeded, update availability
        if response.status_code == 201:
            try:
                availability_payload = {
                    "DoctorID": payload["doctor_id"],
                    "Date": payload["appointment_date"],
                    "StartTime": payload["start_time"].split("T")[1],  # Extract just time
                    "Available": False
                }
                avail_res = requests.post(AVAILABILITY_API_URL + "/update", json=availability_payload)
                if not avail_res.ok:
                    raise Exception("Failed to update doctor availability")
                

                # Step 4: Send both email and SMS notifications about the appointment confirmation
                # Prepare common notification data
                notification_data = {
                    "message": f"Your appointment with doctor {payload['doctor_name']} is confirmed for {payload['appointment_date']} at {payload['start_time']}.",
                    "subject": "Appointment Confirmation"
                }
                
                # Send SMS notification
                sms_notification_data = {
                    **notification_data,
                    "recipient": patient_phone,  # Use phone number for SMS
                    "method": "sms"  # Set the method to SMS
                }
                # Send request to notification API for SMS
                requests.post(NOTIFICATION_API_URL, json=sms_notification_data)

                # Send Email notification
                email_notification_data = {
                    **notification_data,
                    "recipient": patient_email,  # Use email for Email
                    "method": "email"  
                }
                # Send request to notification API for Email
                requests.post(NOTIFICATION_API_URL, json=email_notification_data)

            except Exception as avail_error:
                return jsonify({
                    "code": 500,
                    "message": f"Appointment created but failed to update availability: {str(avail_error)}"
                }), 500

            # Success: return original appointment response
            return jsonify(appointment_result), 201

        # Forward error from appointment service
        return jsonify(appointment_result), response.status_code

    except Exception as e:
        return jsonify({"code": 500, "message": f"Composite service error: {str(e)}"}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)