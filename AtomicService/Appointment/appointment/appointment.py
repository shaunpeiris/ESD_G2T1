from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from os import environ

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
db = SQLAlchemy(app)

class Appointment(db.Model):
    __tablename__ = 'appointment'

    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, nullable=False)
    doctor_id = db.Column(db.String(4), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    appointment_status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, patient_id, doctor_id, appointment_date, start_time, end_time, appointment_status, notes=None):
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.appointment_date = appointment_date
        self.start_time = start_time
        self.end_time = end_time
        self.appointment_status = appointment_status
        self.notes = notes

    def json(self):
        return {
            "appointment_id": self.appointment_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "appointment_date": self.appointment_date.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "appointment_status": self.appointment_status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

# to create appointment
@app.route("/appointment", methods=['POST'])
def create_appointment():
    """Create a new appointment"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['patient_id', 'doctor_id', 'appointment_date', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({
                "code": 400,
                "message": f"Missing required field: {field}"
            }), 400
    
    try:
        # Parse dates and times
        appointment_date = datetime.strptime(data['appointment_date'], "%Y-%m-%d").date()
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
        
        # # Validate time logic
        # if start_time >= end_time:
        #     return jsonify({
        #         "code": 400,
        #         "message": "Start time must be before end time."
        #     }), 400
            
        # # Check doctor availability
        # if not check_availability(data['doctor_id'], start_time, end_time):
        #     return jsonify({
        #         "code": 409,
        #         "message": "Doctor is not available during the requested time."
        #     }), 409
        
        # Create appointment
        appointment = Appointment(
            patient_id=data['patient_id'],
            doctor_id=data['doctor_id'],
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            appointment_status="SCHEDULED",
            notes="New patient consultation"
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            "code": 201,
            "data": appointment.json(),
            "message": "Appointment created successfully."
        }), 201
        
    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": f"Invalid date or time format: {str(e)}"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"An error occurred creating the appointment: {str(e)}"
        }), 500

#to get ALL appointment details for a specific doctor and status is scheduled and the date is for the same day
@app.route("/appointment/doctor/<string:doctor_id>")
def get_doctor_appointments(doctor_id):
    """Get all appointments for a doctor that are scheduled for the current date"""
    current_date = datetime.now().date()
    appointments = db.session.scalars(
        db.select(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_status == "Scheduled",
            Appointment.appointment_date == current_date
        )
    ).all()

    if appointments:
        return jsonify({
            "code": 200,
            "data": {
                "appointments": [appointment.json() for appointment in appointments]
            }
        })
    return jsonify({
        "code": 404,
        "message": f"No scheduled appointments found for doctor {doctor_id} on {current_date}."
    }), 404

#to get patient appointment details via the appointment ID 
@app.route("/appointment/<int:appointment_id>")
def get_appointment(appointment_id):
    """Get a specific appointment by ID"""
    appointment = db.session.scalar(db.select(Appointment).filter_by(appointment_id=appointment_id))

    if appointment:
        return jsonify({
            "code": 200,
            "data": appointment.json()
        })
    return jsonify({
        "code": 404,
        "message": f"Appointment with ID {appointment_id} not found."
    }), 404


# to update appointment notes
@app.route("/appointment/<int:appointment_id>/notes", methods=["PATCH"])
def update_appointment_notes(appointment_id):
    appointment = db.session.scalar(db.select(Appointment).filter_by(appointment_id=appointment_id))
    
    if not appointment:
        return jsonify({
            "code": 404,
            "message": f"Appointment with ID {appointment_id} not found."
        }), 404

    data = request.get_json()
    if "notes" not in data:
        return jsonify({
            "code": 400,
            "message": "Missing required field: notes"
        }), 400

    try:
        appointment.notes = data["notes"]
        db.session.commit()
        return jsonify({
            "code": 200,
            "data": appointment.json(),
            "message": "Appointment notes updated successfully."
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"An error occurred updating appointment notes: {str(e)}"
        }), 500
    
# to update status of appointment to completed after prescription is updated
@app.route("/appointment/<int:appointment_id>/status", methods=["PATCH"])
def update_appointment_status(appointment_id):
    # Retrieve the appointment (assumes it exists)
    appointment = db.session.scalar(db.select(Appointment).filter_by(appointment_id=appointment_id))
    # Update the status to COMPLETED (regardless of its current value)
    appointment.appointment_status = "COMPLETED"
    db.session.commit()
    return jsonify({
        "code": 200,
        "data": appointment.json(),
        "message": "Appointment status updated to COMPLETED."
    }), 200
    


# commenting this because we dont need to find doctor by date
#get appointment details based on the date of an appointment of that specific doctor 
# @app.route("/appointment/doctor/<string:doctor_id>/date/<string:date>")
# def get_doctor_appointments_by_date(doctor_id, date):
#     """Get all appointments for a doctor on a specific date"""
#     try:
#         appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
        
#         appointments = db.session.scalars(
#             db.select(Appointment).filter_by(
#                 doctor_id=doctor_id, 
#                 appointment_date=appointment_date
#             )
#         ).all()

#         if appointments:
#             return jsonify({
#                 "code": 200,
#                 "data": {
#                     "appointments": [appointment.json() for appointment in appointments]
#                 }
#             })
#         return jsonify({
#             "code": 404,
#             "message": f"No appointments found for doctor {doctor_id} on {date}."
#         }), 404
#     except ValueError:
#         return jsonify({
#             "code": 400,
#             "message": "Invalid date format. Please use YYYY-MM-DD format."
#         }), 400
    

# commenting this status is only updated after creating prescription
# #appointment microservice returns ALL appointment details based on the patient id to the doctor management composite UI 
@app.route("/appointment/patient/<int:patient_id>")
def get_patient_appointments(patient_id):
    """Get all appointments for a patient"""
    appointments = db.session.scalars(db.select(Appointment).filter_by(patient_id=patient_id)).all()

    if appointments:
        return jsonify({
            "code": 200,
            "data": {
                "appointments": [appointment.json() for appointment in appointments]
            }
        })
    return jsonify({
        "code": 404,
        "message": f"No appointments found for patient {patient_id}."
    }), 404


# #updates the appointment status - scheduled / completed 
# @app.route("/appointment/<int:appointment_id>/status", methods=['PATCH'])
# def update_appointment_status(appointment_id):
#     """Update appointment status"""
#     appointment = db.session.scalar(db.select(Appointment).filter_by(appointment_id=appointment_id))
    
#     if not appointment:
#         return jsonify({
#             "code": 404,
#             "message": f"Appointment with ID {appointment_id} not found."
#         }), 404
    
#     data = request.get_json()
    
#     if 'status' not in data:
#         return jsonify({
#             "code": 400,
#             "message": "Missing required field: status"
#         }), 400
    
#     valid_statuses = ["ASSIGNED", "COMPLETED"]  
#     if data['status'] not in valid_statuses:
#         return jsonify({
#             "code": 400,
#             "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
#         }), 400
    
#     try:
#         appointment.appointment_status = data['status']
#         db.session.commit()
        
#         return jsonify({
#             "code": 200,
#             "data": appointment.json(),
#             "message": f"Appointment status updated to {data['status']} successfully."
#         })
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             "code": 500,
#             "message": f"An error occurred updating the appointment status: {str(e)}"
#         }), 500


#not part of scenario but this displays all appointments on the UI 
# @app.route("/appointment")
# def get_all_appointments():
#     """Get all appointments"""
#     appointments = db.session.scalars(db.select(Appointment)).all()

#     if appointments:
#         return jsonify({
#             "code": 200,
#             "data": {
#                 "appointments": [appointment.json() for appointment in appointments]
#             }
#         })
#     return jsonify({
#         "code": 404,
#         "message": "No appointments found."
#     }), 404



#not part of scenario but part of UI 


#not part of scenario but part of UI under upcoming appointments 

# Helper functions 
# this ensures that their appointments dont clash 
# def check_availability(doctor_id, start_time, end_time, appointment_id=None):
#     """Check if doctor is available during the specified time"""
#     query = db.select(Appointment).filter(
#         Appointment.doctor_id == doctor_id,
#         Appointment.start_time < end_time,
#         Appointment.end_time > start_time
#     )
    
#     # Exclude current appointment when updating
#     if appointment_id:
#         query = query.filter(Appointment.appointment_id != appointment_id)
        
#     conflicting_appointments = db.session.scalars(query).all()
#     return len(conflicting_appointments) == 0


#part of scenario : create new appointment 
#the patient requests an appointment and the function validates the request & ensures that all required fields are present 
#this function checks doctor's availability using the check_availability function to ensure that the doctor is free 
#once validated, the new appointment is added into the db and assigned the status of "SCHEDULED"



#not part of scenario, maybe can delete 
# @app.route("/appointment/<int:appointment_id>", methods=['DELETE'])
# def delete_appointment(appt_id):
#     """Delete an appointment"""
#     appointment = db.session.scalar(db.select(Appointment).filter_by(appointment_id=appt_id))
    
#     if not appointment:
#         return jsonify({
#             "code": 404,
#             "message": f"Appointment with ID {appt_id} not found."
#         }), 404
    
#     try:
#         db.session.delete(appointment)
#         db.session.commit()
        
#         return jsonify({
#             "code": 200,
#             "message": "Appointment deleted successfully."
#         })
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({
#             "code": 500,
#             "message": f"An error occurred deleting the appointment: {str(e)}"
#         }), 500

if __name__ == '__main__':
    with app.app_context(): #push an application context
        db.create_all() #create table 
    app.run(host='0.0.0.0', port=5002, debug=True)