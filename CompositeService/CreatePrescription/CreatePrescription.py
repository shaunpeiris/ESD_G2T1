from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from invokes import invoke_http
import amqp_connection
import pika
import json

app = Flask(__name__)
CORS(app)

# URLs for microservices
patient_URL = "http://host.docker.internal:5001/patient"
appointment_URL = "http://host.docker.internal:5002/appointment"
prescription_URL = "http://host.docker.internal:5003/prescription"
inventory_URL = "https://personal-dxi3ngjv.outsystemscloud.com/Inventory/rest/v1/inventory"
inventory_name_URL = "https://personal-dxi3ngjv.outsystemscloud.com/Inventory/rest/v1/inventory/name"

@app.route("/create_prescription", methods=['POST'])
def create_prescription():
    if request.is_json:
        try:
            prescription_data = request.get_json()
            print("\nReceived a prescription in JSON:", prescription_data)

            # do the actual work
            # 1. Process the prescription data
            result = processCreatePrescription(prescription_data)
            return jsonify(result), result["code"]

        except Exception as e:
            # Unexpected error in code
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "create_prescription.py internal error: " + ex_str
            }), 500
            
    # if reached here, not a JSON request.
    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400

def check_allergies(medicines, allergies):
    """
    Check for allergies in the prescription
    
    Args:
        medicines: List of medicine objects with name details
        allergies: List of patient allergies
    
    Returns:
        tuple: (is_allergic, list_of_allergic_medicines)
    """
    allergic_medicines = []
    
    # If no allergies, return immediately
    if not allergies:
        return False, []
    
    # Check each medicine name against allergies
    for medicine in medicines:
        medicine_name = medicine["name"]
        
        # Check if medicine name is in allergies list
        if medicine_name in allergies:
            allergic_medicines.append(medicine_name)
            
    return len(allergic_medicines) > 0, allergic_medicines

def processCreatePrescription(prescription_data):
    # Extract appointment ID from the prescription data
    appointment_id = prescription_data["appointment_id"]
    
    # 1. Get appointment details to retrieve patient ID and doctor ID
    print('\n-----Invoking appointment microservice-----')
    appointment_result = invoke_http(f"{appointment_URL}/{appointment_id}", method='GET')
    print('appointment_result:', appointment_result)
    
    # Check if appointment exists
    if appointment_result["code"] != 200:
        return {
            "code": 404,
            "message": f"Appointment not found: {appointment_id}"
        }
    
    # Extract patient ID and doctor ID from appointment
    # Adjusting for the database column names in your appointment table
    patient_id = appointment_result["data"]["patient_id"]
    doctor_id = appointment_result["data"]["doctor_id"]
    
    # Update prescription data with patient and doctor IDs
    prescription_data["patient_id"] = patient_id
    prescription_data["doctor_id"] = doctor_id
    
    # 2. Get patient allergies
    print('\n-----Invoking patient microservice-----')
    patient_result = invoke_http(f"{patient_URL}/{patient_id}", method='GET')
    print('patient_result:', patient_result)
    
    if patient_result["code"] != 200:
        return {
            "code": 404,
            "message": f"Patient not found: {patient_id}"
        }
    
    # Extract allergies from patient data
    allergies = []
    if patient_result["data"]["medicalHistory"]:
        # In case medicalHistory is returned as a string instead of a parsed JSON object
        medical_history = patient_result["data"]["medicalHistory"]
        if isinstance(medical_history, str):
            try:
                medical_history = json.loads(medical_history)
            except json.JSONDecodeError:
                print("Error decoding medicalHistory JSON string")
                medical_history = {}
        
        # Now extract allergies from the medicalHistory
        if isinstance(medical_history, dict) and "allergies" in medical_history:
            allergies = medical_history["allergies"]
    
    # 3. Get medicine IDs from names and prepare prescription check data
    formatted_medicines = []
    for medicine in prescription_data["medicine"]:
        if "quantity" not in medicine:
            # Default to 1 if quantity not specified, or set an appropriate default
            medicine["quantity"] = 1
            
        medicine_name = medicine["name"]
        # Get medicine details from inventory by name
        print(f'\n-----Invoking inventory microservice for {medicine_name}-----')
        inventory_result = invoke_http(f"{inventory_name_URL}/{medicine_name}", method='GET')
        print('inventory_result:', inventory_result)
        
        if inventory_result["Result"]["success"] and len(inventory_result["Medications"]) > 0:
            medication = inventory_result["Medications"][0]
            # Use medicationID from inventory system (correct casing)
            medicine["medicineID"] = medication["medicationID"]
            
            # Add the medicine with updated info to our list
            formatted_medicines.append({
                "name": medicine["name"],
                "dose": medicine.get("dose", ""),
                "frequency": medicine.get("frequency", ""),
                "medicineID": medication["medicationID"],
                "quantity": medicine["quantity"]
            })
        else:
            return {
                "code": 404,
                "message": f"Medicine not found: {medicine_name}"
            }
    
    # 4. Check for allergies
    print('\n-----Checking for allergies-----')
    is_allergic, allergic_medicines = check_allergies(formatted_medicines, allergies)
    
    # If allergic, return the allergic medicines
    if is_allergic:
        return {
            "code": 400,
            "data": {
                "allergic_medicine": allergic_medicines,
            },
            "message": "Allergic medicine found"
        }
    
    # 5. Create prescription record
    # Format the medicine data to match your database structure
# With this simpler version:
    formatted_prescription_data = {
        "appointmentID": appointment_id,
        "appointment_id": appointment_id,
        "medicine": formatted_medicines,  # Include "medicine" key
        "medications": formatted_medicines  # Also include "medications" key
    }
    print('\n-----Debug: Formatted prescription data-----')
    print(json.dumps(formatted_prescription_data, indent=2))

    print('\n-----Invoking prescription microservice to create prescription-----')
    prescription_result = invoke_http(prescription_URL, method='POST', json=formatted_prescription_data)
    print('prescription_result:', prescription_result)
        
    code = prescription_result["code"]
    if code not in range(200, 300):
        return {
            "code": 500,
            "data": {"prescription_result": prescription_result},
            "message": "Error creating prescription"
        }
    
    # 6. Extract and send prescription ID to AMQP broker
    print('\n-----Sending prescription ID to AMQP broker-----')
    exchangename = "dispenser_direct"  # exchange name
    connection = amqp_connection.create_connection() 
    channel = connection.channel()
    
    # Ensure the exchange exists
    channel.exchange_declare(exchange=exchangename, exchange_type='direct', durable=True)
    
    # Improved prescription ID extraction
    prescription_id = None
    if prescription_result.get('data') and isinstance(prescription_result['data'], dict):
        # Try all possible keys where the ID might be stored
        possible_id_keys = ['id', 'prescription_id', 'prescriptionID', 'PrescriptionID']
        for key in possible_id_keys:
            if key in prescription_result['data']:
                prescription_id = prescription_result['data'][key]
                break
                
        # Debug print to help identify the actual structure
        if not prescription_id:
            print("Could not find prescription ID. Data structure:", json.dumps(prescription_result['data'], indent=2))

    if prescription_id:
        message = json.dumps({"prescription_id": prescription_id})
        channel.basic_publish(
            exchange=exchangename, 
            routing_key="prescription.id", 
            body=message, 
            properties=pika.BasicProperties(delivery_mode=2)
        ) 
        print(f"Prescription ID {prescription_id} sent to AMQP broker")
    else:
        print("WARNING: No prescription ID found in the response, nothing sent to AMQP broker")
        
    # 7. Return prescription result
    return {
        "code": 201,
        "data": {
            "prescription_result": prescription_result["data"]
        },
        "message": "Prescription created successfully"
    }

# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) +
          " for creating prescription...")
    app.run(host="0.0.0.0", port=6003, debug=True)