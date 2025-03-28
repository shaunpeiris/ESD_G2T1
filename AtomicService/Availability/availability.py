from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, firestore
import socket


# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("./serviceAccountKey.json")  # Replace with your Firebase service account key file
firebase_admin.initialize_app(cred)

# Get Firestore database instance
db = firestore.client()

@app.route("/whoami")
def whoami():
    return f"Hi from container: {socket.gethostname()}"

# Route to get all doctor availabilities & also filter based on DoctorID &/OR Date &/OR StartTime
@app.route('/doctor_availabilities', methods=['GET'])
def get_availabilities():
    try:
        doctor_id = request.args.get("doctor_id")
        date = request.args.get("date")
        start_time = request.args.get("start_time")

        ref = db.collection("Doctor_Availability")
        query = ref

        # Apply filters only if provided
        if doctor_id:
            query = query.where("DoctorID", "==", doctor_id)
        if date:
            query = query.where("Date", "==", date)
        if start_time:
            query = query.where("StartTime", "==", start_time)

        docs = query.stream()
        results = [doc.to_dict() for doc in docs]

        if not results:
            return jsonify({
                "success": False,
                "message": "No matching availabilities found."
            }), 404

        return jsonify({
            "success": True,
            "filters": {
                "doctor_id": doctor_id,
                "date": date,
                "start_time": start_time
            },
            "count": len(results),
            "data": results
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    

# 🔄 Route to update availability to False
@app.route('/doctor_availabilities/update', methods=['POST'])
def update_doctor_availability():
    try:
        data = request.get_json()

        # Required fields
        doctor_id = data.get("DoctorID")
        date = data.get("Date")
        start_time = data.get("StartTime")
        available = data.get("Available")

        if not (doctor_id and date and start_time):
            return jsonify({"success": False, "message": "DoctorID, Date, and StartTime are required."}), 400

        # Search for the matching document
        ref = db.collection("Doctor_Availability")
        query = ref.where("DoctorID", "==", doctor_id)\
                   .where("Date", "==", date)\
                   .where("StartTime", "==", start_time)
        docs = query.stream()

        updated = False
        for doc in docs:
            doc_ref = ref.document(doc.id)
            doc_ref.update({"Available": available})
            updated = True

        if not updated:
            return jsonify({"success": False, "message": "No matching slot found."}), 404

        return jsonify({"success": True, "message": "Availability updated to " + str(available).capitalize() + "."}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Run the Flask server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
