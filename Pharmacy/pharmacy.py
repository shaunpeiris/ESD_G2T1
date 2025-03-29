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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions and decorators
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
    """Create a standardized JSON response"""
    response = {"code": code}
    if message:
        response["message"] = message
    if data:
        response["data"] = data
    return jsonify(response), code

def make_api_request(method, url, json=None, timeout=5):
    """Make an API request with standardized error handling"""
    try:
        response = requests.request(
            method=method,
            url=url,
            json=json,
            timeout=timeout
        )
        return response
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        raise

@lru_cache(maxsize=128)
def get_cached_inventory(medication_name):
    """Cached inventory lookup with 2-second timeout"""
    try:
        response = make_api_request(
            'GET',
            f"{INVENTORY_API_BASE_URL}/inventory/name/{medication_name}/",
            timeout=2
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"Inventory API error for {medication_name}: {str(e)}")
        return None

def get_inventory_data(medication_name):
    """Helper function to get complete inventory data for a medication"""
    response = get_cached_inventory(medication_name)
    if not response or 'Medications' not in response or not response['Medications']:
        return None
    return response['Medications'][0]

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present in the data"""
    if not all(field in data for field in required_fields):
        return False, f"Missing required fields. Required: {', '.join(required_fields)}"
    return True, None

def update_inventory(medication_data):
    """Update inventory with medication data"""
    required_fields = ['medicationID', 'medicationName', 'quantity', 'price']
    
    is_valid, error_message = validate_required_fields(medication_data, required_fields)
    if not is_valid:
        return None, 400, error_message
    
    response = make_api_request(
        'PUT',
        f"{INVENTORY_API_BASE_URL}/inventory",
        json=medication_data
    )
    
    # Check for API-level success
    if response.status_code != 200:
        return None, response.status_code, f"Inventory API error: {response.text}"
    
    # Check for business-level success
    result = response.json()
    if not result.get('success', False):
        return None, 500, result.get('errorMessage', 'Unknown error')
    
    return result, 200, "Inventory updated successfully"

def get_prescription_data(prescription_id):
    """Get prescription data from the prescription service"""
    response = make_api_request(
        'GET',
        f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}"
    )
    
    if response.status_code != 200:
        return None, response.status_code, f"Prescription service error: {response.text}"
    
    prescription_data = response.json().get('data', {})
    return prescription_data, 200, "Prescription retrieved successfully"

def update_prescription_status(prescription_id, status):
    """Update the status of a prescription"""
    response = make_api_request(
        'PUT',
        f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}/status",
        json={"status": status}
    )
    
    if response.status_code != 200:
        return None, response.status_code, f"Prescription status update failed: {response.text}"
    
    result = response.json()
    return result, 200, "Prescription status updated successfully"

# API Routes
@app.route("/pharmacy/inventory", methods=['GET'])
@handle_api_error
def list_all_medications():
    """Get list of all medications from inventory"""
    response = make_api_request('GET', f"{INVENTORY_API_BASE_URL}/inventory")
    return jsonify(response.json()), response.status_code

@app.route("/pharmacy/inventory/<medication_name>", methods=['GET'])
@handle_api_error
def get_medication_by_name(medication_name):
    """Get details for a specific medication by name"""
    response = make_api_request('GET', f"{INVENTORY_API_BASE_URL}/inventory/name/{medication_name}/")
    return jsonify(response.json()), response.status_code

@app.route("/pharmacy/inventory", methods=['PUT'])
@handle_api_error
def update_medication_quantity():
    """Update medication details in inventory"""
    data = request.json
    result, status_code, message = update_inventory(data)
    
    if status_code != 200:
        return create_response(status_code, message)
    
    return jsonify(result), status_code

@app.route("/pharmacy/prescription/<prescription_id>", methods=['GET'])
@handle_api_error
def get_prescription(prescription_id):
    """Retrieve prescription details with pharmacy processing info"""
    prescription_data, status_code, message = get_prescription_data(prescription_id)
    
    if status_code != 200:
        return create_response(status_code, message)
    
    # Add pharmacy processing information
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
    """Process prescription dispensing with inventory updates"""
    # Retrieve prescription details
    prescription_response = requests.get(
        f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}",
        timeout=5
    )
    
    if prescription_response.status_code != 200:
        error_msg = f"Prescription {prescription_id} not found"
        logger.error(error_msg)
        return jsonify({"code": 404, "message": error_msg}), 404

    prescription_data = prescription_response.json().get('data', {})
    
    # Check if prescription has already been dispensed
    if prescription_data.get('status', False):
        error_msg = f"Prescription {prescription_id} has already been dispensed"
        logger.warning(error_msg)
        return jsonify({"code": 400, "message": error_msg}), 400
    
    medications = prescription_data.get('medicine', [])
    
    if not isinstance(medications, list):
        error_msg = "Invalid medications format in prescription"
        logger.error(error_msg)
        return jsonify({"code": 400, "message": error_msg}), 400

    inventory_updates = []
    for med in medications:
        # Validate medication format
        if not isinstance(med, dict) or 'name' not in med or 'quantity' not in med:
            return create_response(400, f"Invalid medication format: {med}")
        
        med_name = med['name']
        required_qty = med['quantity']
        
        # Get current inventory state
        inventory_data = get_inventory_data(med_name)
        if not inventory_data:
            return create_response(404, f"Medication {med_name} not found in inventory")

        current_stock = inventory_data.get('quantity', 0)
        med_id = inventory_data.get('medicationID', '')
        med_price = inventory_data.get('price', 0.0)
        
        # Check stock availability
        if current_stock < required_qty:
            return create_response(400, f"Insufficient stock for {med_name}. Required: {required_qty}, Available: {current_stock}")

        # Calculate new quantity
        new_quantity = current_stock - required_qty
        
        # Update inventory
        med_update_data = {
            "medicationID": med_id,
            "medicationName": med_name,
            "quantity": new_quantity,
            "price": med_price
        }

        result, status_code, message = update_inventory(med_update_data)
        
        if status_code != 200:
            return create_response(status_code, message)

        inventory_updates.append({
            "medication": med_name,
            "medicationID": med_id,
            "previous_quantity": current_stock,
            "new_quantity": new_quantity,
            "price": med_price
        })
    
    # Update prescription status
    result, status_code, message = update_prescription_status(prescription_id, True)
    
    if status_code != 200:
        return create_response(500, "Prescription dispensed but status update failed")

    return create_response(
        200, 
        "Prescription dispensed successfully", 
        {
            "prescription_id": prescription_id,
            "inventory_updates": inventory_updates
        }
    )




if __name__ == '__main__':
    logger.info("Starting Pharmacy Service")
    app.run(host='0.0.0.0', port=5004, debug=False)
