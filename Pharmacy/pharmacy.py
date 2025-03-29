from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import logging
from functools import lru_cache, wraps

app = Flask(__name__)
CORS(app)

INVENTORY_API_BASE_URL = os.environ.get('INVENTORY_API_BASE_URL', "https://personal-dxi3ngjv.outsystemscloud.com/Inventory/rest/v1")
PRESCRIPTION_SERVICE_URL = os.environ.get('PRESCRIPTION_SERVICE_URL', 'http://prescription:5003')
BILLING_SERVICE_URL = os.environ.get('BILLING_SERVICE_URL', 'http://billing:5024')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_api_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as re:
            logger.error(f"Network error: {str(re)}")
            return create_response(503, "Service unavailable")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return create_response(500, f"Internal server error: {str(e)}")
    return wrapper

def create_response(code, message=None, data=None):
    response = {"code": code}
    if message:
        response["message"] = message
    if data:
        response["data"] = data
    return jsonify(response), code

def make_api_request(method, url, json=None, timeout=5):
    try:
        response = requests.request(method=method, url=url, json=json, timeout=timeout)
        return response
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        raise

@lru_cache(maxsize=128)
def get_cached_inventory(medication_name):
    try:
        response = make_api_request('GET', f"{INVENTORY_API_BASE_URL}/inventory/name/{medication_name}/", timeout=2)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"Inventory API error for {medication_name}: {str(e)}")
        return None

def get_inventory_data(medication_name):
    response = get_cached_inventory(medication_name)
    if not response or 'Medications' not in response or not response['Medications']:
        return None
    return response['Medications'][0]

def validate_required_fields(data, required_fields):
    if not all(field in data for field in required_fields):
        return False, f"Missing required fields. Required: {', '.join(required_fields)}"
    return True, None

def update_inventory(medication_data):
    required_fields = ['medicationID', 'medicationName', 'quantity', 'price']
    is_valid, error_message = validate_required_fields(medication_data, required_fields)
    if not is_valid:
        return None, 400, error_message
    
    response = make_api_request('PUT', f"{INVENTORY_API_BASE_URL}/inventory", json=medication_data)
    
    if response.status_code != 200:
        return None, response.status_code, f"Inventory API error: {response.text}"
    
    result = response.json()
    if not result.get('success', False):
        return None, 500, result.get('errorMessage', 'Unknown error')
    
    return result, 200, "Inventory updated successfully"

def get_prescription_data(prescription_id):
    response = make_api_request('GET', f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}")
    
    if response.status_code != 200:
        return None, response.status_code, f"Prescription service error: {response.text}"
    
    prescription_data = response.json().get('data', {})
    return prescription_data, 200, "Prescription retrieved successfully"

def update_prescription_status(prescription_id, status):
    response = make_api_request('PUT', f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}/status", json={"status": status})
    
    if response.status_code != 200:
        return None, response.status_code, f"Prescription status update failed: {response.text}"
    
    result = response.json()
    return result, 200, "Prescription status updated successfully"

def create_billing_session(prescription_id, appointment_id, medications):
    """
    Create a billing session by calling the billing microservice
    
    Args:
        prescription_id: ID of the prescription
        appointment_id: ID of the appointment
        medications: List of medications with prices
    
    Returns:
        tuple: (success, message, checkout_url)
    """
    try:
        # Step 1: Get appointment data to retrieve patient ID
        appointment_data, status_code, message = get_appointment_data(appointment_id)
        
        if status_code != 200:
            logger.error(f"Failed to get appointment data: {message}")
            return False, f"Failed to get appointment data: {message}", None
        
        # Step 2: Extract patient ID from appointment data
        patient_id = appointment_data.get('patient_id')
        if not patient_id:
            logger.error(f"Patient ID not found in appointment data for appointment {appointment_id}")
            return False, f"Patient ID not found in appointment data for appointment {appointment_id}", None
        
        logger.info(f"Retrieved patient ID {patient_id} from appointment {appointment_id}")
        
        # Step 3: Get patient details using the patient ID
        patient_data, status_code, message = get_patient_data(patient_id)
        
        if status_code != 200:
            logger.error(f"Failed to get patient data for ID {patient_id}: {message}")
            return False, f"Failed to get patient data: {message}", None
        
        # Step 4: Extract patient email
        patient_email = patient_data.get('email')
        if not patient_email:
            logger.error(f"Email not found for patient {patient_id}")
            return False, f"Patient email not found for patient {patient_id}", None
        
        logger.info(f"Retrieved email for patient {patient_id}")
        
        # Step 5: Prepare request data for billing service
        billing_data = {
            "prescription_id": prescription_id,
            "patient_id": patient_id,
            "patient_email": patient_email,
            "medicines": medications
        }
        
        # Step 6: Call the billing service
        try:
            response = requests.post(
                f"{BILLING_SERVICE_URL}/create-checkout-session",
                json=billing_data,
                timeout=5
            )
            
            # Step 7: Handle billing service response
            if response.status_code != 200:
                error_msg = f"Billing service error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg, None
                
            checkout_url = response.json().get("url")
            if not checkout_url:
                logger.error("Billing service did not return a checkout URL")
                return False, "Billing service did not return a checkout URL", None
                
            logger.info(f"Successfully created billing session for prescription {prescription_id}")
            return True, "Billing session created successfully", checkout_url
            
        except requests.exceptions.Timeout:
            error_msg = "Timeout while connecting to billing service"
            logger.error(error_msg)
            return False, error_msg, None
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error while connecting to billing service"
            logger.error(error_msg)
            return False, error_msg, None
            
    except Exception as e:
        error_msg = f"Unexpected error in create_billing_session: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, None



def get_appointment_data(appointment_id):
    """
    Fetch appointment data from the appointment microservice
    
    Args:
        appointment_id: ID of the appointment
    
    Returns:
        tuple: (appointment_data, status_code, message)
    """
    try:
        APPOINTMENT_SERVICE_URL = os.environ.get('APPOINTMENT_SERVICE_URL', 'http://appointment:5002')
        response = make_api_request('GET', f"{APPOINTMENT_SERVICE_URL}/appointment/{appointment_id}")
        
        if response.status_code != 200:
            error_msg = f"Appointment service error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return None, response.status_code, error_msg
        
        result = response.json()
        if result.get('code') != 200:
            error_msg = f"Appointment data retrieval failed: {result.get('message', 'Unknown error')}"
            logger.error(error_msg)
            return None, result.get('code', 500), error_msg
        
        appointment_data = result.get('data', {})
        return appointment_data, 200, "Appointment data retrieved successfully"
    except requests.exceptions.RequestException as e:
        error_msg = f"Error connecting to appointment service: {str(e)}"
        logger.error(error_msg)
        return None, 503, error_msg


def get_patient_data(patient_id):
    """
    Fetch patient data from the patient microservice
    
    Args:
        patient_id: ID of the patient
    
    Returns:
        tuple: (patient_data, status_code, message)
    """
    try:
        PATIENT_SERVICE_URL = os.environ.get('PATIENT_SERVICE_URL', 'http://patient:5001')
        response = make_api_request('GET', f"{PATIENT_SERVICE_URL}/patient/{patient_id}")
        
        if response.status_code != 200:
            error_msg = f"Patient service error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return None, response.status_code, error_msg
        
        result = response.json()
        if result.get('code') != 200:
            error_msg = f"Patient data retrieval failed: {result.get('message', 'Unknown error')}"
            logger.error(error_msg)
            return None, result.get('code', 500), error_msg
        
        patient_data = result.get('data', {})
        return patient_data, 200, "Patient data retrieved successfully"
    except requests.exceptions.RequestException as e:
        error_msg = f"Error connecting to patient service: {str(e)}"
        logger.error(error_msg)
        return None, 503, error_msg


@app.route("/pharmacy/inventory", methods=['GET'])
@handle_api_error
def list_all_medications():
    response = make_api_request('GET', f"{INVENTORY_API_BASE_URL}/inventory")
    return jsonify(response.json()), response.status_code

@app.route("/pharmacy/inventory/<medication_name>", methods=['GET'])
@handle_api_error
def get_medication_by_name(medication_name):
    response = make_api_request('GET', f"{INVENTORY_API_BASE_URL}/inventory/name/{medication_name}/")
    return jsonify(response.json()), response.status_code

@app.route("/pharmacy/inventory", methods=['PUT'])
@handle_api_error
def update_medication_quantity():
    data = request.json
    result, status_code, message = update_inventory(data)
    
    if status_code != 200:
        return create_response(status_code, message)
    
    return jsonify(result), status_code

@app.route("/pharmacy/prescription/<prescription_id>", methods=['GET'])
@handle_api_error
def get_prescription(prescription_id):
    prescription_data, status_code, message = get_prescription_data(prescription_id)
    
    if status_code != 200:
        return create_response(status_code, message)
    
    prescription_data.update({
        "pharmacy_info": {
            "processing_status": "ready_for_pickup",
            "estimated_pickup_time": "2025-03-29T10:00:00+08:00",
            "pharmacy_notes": "Please bring your ID for verification"
        }
    })
    
    return create_response(200, data=prescription_data)

@app.route("/pharmacy/prescription/<prescription_id>/dispense", methods=['POST'])
@handle_api_error
def dispense_prescription(prescription_id):
    """Process prescription dispensing with billing first, then inventory updates"""
    prescription_data, status_code, message = get_prescription_data(prescription_id)
    
    if status_code != 200:
        return create_response(404, f"Prescription {prescription_id} not found")

    if prescription_data.get('status', False):
        return create_response(400, f"Prescription {prescription_id} has already been dispensed")
    
    medications = prescription_data.get('medicine', [])
    
    if not isinstance(medications, list):
        return create_response(400, "Invalid medications format in prescription")

    # First validate all medications without updating inventory
    medication_updates = []
    payment_medications = []
    
    for med in medications:
        # Validate medication without updating inventory
        validation_result, status_code, message = validate_medication(med)
        if status_code != 200:
            return create_response(status_code, message)
        medication_updates.append(validation_result)
        payment_medications.append({
            "medication": validation_result["medication"],
            "price": int(validation_result["price"] * 100)  # Convert to cents for Stripe
        })
    
    # Get appointment ID from prescription data
    appointment_id = prescription_data.get('appointment_id')
    if not appointment_id:
        return create_response(400, "Appointment ID not found in prescription data")
    
    # Create payment session using appointment_id BEFORE updating inventory
    payment_success, payment_message, checkout_url = create_billing_session(
        prescription_id, 
        appointment_id,
        payment_medications
    )
    
    if not payment_success:
        logger.error(f"Billing session creation failed: {payment_message}")
        return create_response(500, f"Billing failed: {payment_message}")
    
    # Only update inventory AFTER successful billing URL generation
    inventory_updates = []
    for update in medication_updates:
        # Now actually update the inventory
        med_update_data = {
            "medicationID": update["medicationID"],
            "medicationName": update["medication"],
            "quantity": update["new_quantity"],
            "price": update["price"]
        }
        
        result, status_code, message = update_inventory(med_update_data)
        if status_code != 200:
            logger.error(f"Inventory update failed after successful billing: {message}")
            return create_response(500, f"Billing successful but inventory update failed: {message}")
            
        inventory_updates.append({
            "medication": update["medication"],
            "medicationID": update["medicationID"],
            "previous_quantity": update["current_stock"],
            "new_quantity": update["new_quantity"],
            "price": update["price"]
        })
    
    # Update prescription status after successful billing and inventory updates
    status_result, status_code, status_message = update_prescription_status(prescription_id, True)
    if status_code != 200:
        logger.error(f"Prescription status update failed: {status_message}")
        return create_response(500, f"Billing and inventory updated, but status update failed: {status_message}")
    
    response_data = {
        "prescription_id": prescription_id,
        "inventory_updates": inventory_updates,
        "payment_url": checkout_url
    }
    
    logger.info(f"Prescription {prescription_id} successfully billed and dispensed")
    return create_response(200, "Prescription billed and dispensed successfully", response_data)

def validate_medication(med):
    """Validate a medication without updating inventory"""
    if not isinstance(med, dict) or 'name' not in med or 'quantity' not in med:
        return None, 400, f"Invalid medication format: {med}"
    
    med_name = med['name']
    required_qty = med['quantity']
    
    inventory_data = get_inventory_data(med_name)
    if not inventory_data:
        return None, 404, f"Medication {med_name} not found in inventory"

    current_stock = inventory_data.get('quantity', 0)
    med_id = inventory_data.get('medicationID', '')
    med_price = inventory_data.get('price', 0.0)
    
    if current_stock < required_qty:
        return None, 400, f"Insufficient stock for {med_name}. Required: {required_qty}, Available: {current_stock}"

    new_quantity = current_stock - required_qty
    
    return {
        "medication": med_name,
        "medicationID": med_id,
        "current_stock": current_stock,
        "new_quantity": new_quantity,
        "price": med_price
    }, 200, "Medication validated successfully"



def process_medication(med):
    """Process a single medication for dispensing"""
    if not isinstance(med, dict) or 'name' not in med or 'quantity' not in med:
        return None, 400, f"Invalid medication format: {med}"
    
    med_name = med['name']
    required_qty = med['quantity']
    
    inventory_data = get_inventory_data(med_name)
    if not inventory_data:
        return None, 404, f"Medication {med_name} not found in inventory"

    current_stock = inventory_data.get('quantity', 0)
    med_id = inventory_data.get('medicationID', '')
    med_price = inventory_data.get('price', 0.0)
    
    if current_stock < required_qty:
        return None, 400, f"Insufficient stock for {med_name}. Required: {required_qty}, Available: {current_stock}"

    new_quantity = current_stock - required_qty
    
    med_update_data = {
        "medicationID": med_id,
        "medicationName": med_name,
        "quantity": new_quantity,
        "price": med_price
    }

    result, status_code, message = update_inventory(med_update_data)
    
    if status_code != 200:
        return None, status_code, f"Inventory update failed for {med_name}: {message}"

    return {
        'inventory_update': {
            "medication": med_name,
            "medicationID": med_id,
            "previous_quantity": current_stock,
            "new_quantity": new_quantity,
            "price": med_price
        },
        'payment_info': {
            "medication": med_name,
            "price": int(med_price * 100)  # Convert to cents and ensure it's an integer
        }
    }, 200, "Medication processed successfully"


if __name__ == '__main__':
    logger.info("Starting Pharmacy Service")
    app.run(host='0.0.0.0', port=5004, debug=False)
