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

def create_billing_session(prescription_id, patient_id, medications):
    """
    Create a billing session by calling the billing microservice
    
    Args:
        prescription_id: ID of the prescription
        patient_id: ID of the patient
        medications: List of medications with prices
    
    Returns:
        tuple: (success, message, checkout_url)
    """
    try:
        # First, get patient data to retrieve email
        patient_data, status_code, message = get_patient_data(patient_id)
        
        if status_code != 200:
            return False, f"Failed to get patient data: {message}", None
        
        patient_email = patient_data.get('email')
        if not patient_email:
            return False, "Patient email not found", None
        
        # Now call the billing service with complete information
        response = requests.post(
            f"{BILLING_SERVICE_URL}/create-checkout-session",
            json={
                "prescription_id": prescription_id,
                "patient_id": patient_id,
                "patient_email": patient_email,
                "medicines": medications
            },
            timeout=5
        )
        
        if response.status_code != 200:
            error_msg = f"Billing service error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return False, error_msg, None
            
        return True, "Billing session created successfully", response.json().get("url")
    except requests.exceptions.RequestException as e:
        error_msg = f"Error connecting to billing service: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, None


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
    """Process prescription dispensing with inventory updates and billing"""
    prescription_data, status_code, message = get_prescription_data(prescription_id)
    
    if status_code != 200:
        return create_response(404, f"Prescription {prescription_id} not found")

    if prescription_data.get('status', False):
        return create_response(400, f"Prescription {prescription_id} has already been dispensed")
    
    medications = prescription_data.get('medicine', [])
    
    if not isinstance(medications, list):
        return create_response(400, "Invalid medications format in prescription")

    inventory_updates = []
    payment_medications = []
    
    for med in medications:
        # Validate and process each medication
        result, status_code, message = process_medication(med)
        if status_code != 200:
            return create_response(status_code, message)
        inventory_updates.append(result['inventory_update'])
        payment_medications.append(result['payment_info'])
    
    # Get patient ID from prescription data
    patient_id = prescription_data.get('appointment_id')  # Assuming appointment_id is linked to patient
    
    # Create payment session
    payment_success, payment_message, checkout_url = create_billing_session(
        prescription_id, 
        patient_id,
        payment_medications
    )
    
    if not payment_success:
        logger.error(f"Billing session creation failed: {payment_message}")
        return create_response(500, f"Prescription dispensed but billing failed: {payment_message}")
    
    # Update prescription status only if billing is successful
    status_result, status_code, status_message = update_prescription_status(prescription_id, True)
    if status_code != 200:
        logger.error(f"Prescription status update failed: {status_message}")
        return create_response(500, f"Prescription dispensed and billed, but status update failed: {status_message}")
    
    response_data = {
        "prescription_id": prescription_id,
        "inventory_updates": inventory_updates,
        "payment_url": checkout_url
    }
    
    logger.info(f"Prescription {prescription_id} successfully dispensed and billed")
    return create_response(200, "Prescription dispensed and billed successfully", response_data)

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
