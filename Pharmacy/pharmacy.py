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

def handle_api_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as re:
            logger.error(f"Network error: {str(re)}")
            return jsonify({"code": 503, "message": "Service unavailable"}), 503
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({"code": 500, "message": f"Internal server error: {str(e)}"}), 500
    return wrapper

def get_inventory_data(medication_name):
    """Helper function to get complete inventory data for a medication"""
    response = get_cached_inventory(medication_name)
    if not response or 'Medications' not in response or not response['Medications']:
        return None
    return response['Medications'][0]

@app.route("/pharmacy/inventory", methods=['GET'])
@handle_api_error
def list_all_medications():
    """Get list of all medications from inventory"""
    response = requests.get(f"{INVENTORY_API_BASE_URL}/inventory")
    return jsonify(response.json()), response.status_code

@app.route("/pharmacy/inventory/<medication_name>", methods=['GET'])
@handle_api_error
def get_medication_by_name(medication_name):
    """Get details for a specific medication by name"""
    response = requests.get(f"{INVENTORY_API_BASE_URL}/inventory/name/{medication_name}/")
    return jsonify(response.json()), response.status_code

@app.route("/pharmacy/inventory", methods=['PUT'])
@handle_api_error
def update_medication_quantity():
    """Update medication details in inventory"""
    data = request.json
    required_fields = ['medicationID', 'medicationName', 'quantity', 'price']
    
    if not all(field in data for field in required_fields):
        return jsonify({
            "code": 400,
            "message": f"Missing required fields. Required: {', '.join(required_fields)}"
        }), 400
    
    response = requests.put(
        f"{INVENTORY_API_BASE_URL}/inventory",
        json=data  
    )
    return jsonify(response.json()), response.status_code


@lru_cache(maxsize=128)
def get_cached_inventory(medication_name):
    """Cached inventory lookup with 2-second timeout"""
    try:
        response = requests.get(
            f"{INVENTORY_API_BASE_URL}/inventory/name/{medication_name}/",
            timeout=2
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"Inventory API error for {medication_name}: {str(e)}")
        return None

@app.route("/pharmacy/prescription/<prescription_id>", methods=['GET'])
@handle_api_error
def get_prescription(prescription_id):
    """Retrieve prescription details with pharmacy processing info"""
    prescription_url = f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}"
    response = requests.get(prescription_url, timeout=5)
    
    if response.status_code != 200:
        error_msg = f"Prescription service error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        return jsonify({"code": response.status_code, "message": error_msg}), response.status_code
    
    prescription_data = response.json()
    
    # Add pharmacy processing information
    prescription_data.setdefault("data", {}).update({
        "pharmacy_info": {
            "processing_status": "ready_for_pickup",
            "estimated_pickup_time": "2025-03-29T10:00:00+08:00",
            "pharmacy_notes": "Please bring your ID for verification"
        }
    })
    
    return jsonify(prescription_data), 200

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
    medications = prescription_data.get('medicine', [])
    
    if not isinstance(medications, list):
        error_msg = "Invalid medications format in prescription"
        logger.error(error_msg)
        return jsonify({"code": 400, "message": error_msg}), 400

    inventory_updates = []
    for med in medications:
        # Validate medication format
        if not isinstance(med, dict) or 'name' not in med or 'quantity' not in med:
            error_msg = f"Invalid medication format: {med}"
            logger.error(error_msg)
            return jsonify({"code": 400, "message": error_msg}), 400
        
        med_name = med['name']
        required_qty = med['quantity']
        
        # Get current inventory state
        inventory_data = get_inventory_data(med_name)
        if not inventory_data:
            error_msg = f"Medication {med_name} not found in inventory"
            logger.error(error_msg)
            return jsonify({"code": 404, "message": error_msg}), 404

        current_stock = inventory_data.get('quantity', 0)
        med_id = inventory_data.get('medicationID', '')
        med_price = inventory_data.get('price', 0.0)
        
        # Check stock availability
        if current_stock < required_qty:
            error_msg = f"Insufficient stock for {med_name}. Required: {required_qty}, Available: {current_stock}"
            logger.warning(error_msg)
            return jsonify({"code": 400, "message": error_msg}), 400

        # Calculate new quantity
        new_quantity = current_stock - required_qty
        
        # Update inventory
        med_update_data = {
            "medicationID": med_id,
            "medicationName": med_name,
            "quantity": new_quantity,
            "price": med_price
        }

        update_response = requests.put(
            f"http://localhost:5004/pharmacy/inventory",  # Call our own endpoint
            json=med_update_data,
            timeout=3
        )
        
        if update_response.status_code != 200:
            error_msg = f"Inventory update failed for {med_name}: {update_response.text}"
            logger.error(error_msg)
            return jsonify({"code": 500, "message": error_msg}), 500

        # Check the response content for success status
        update_result = update_response.json()
        if not update_result.get('success', False):
            error_msg = f"Inventory update failed for {med_name}: {update_result.get('errorMessage', 'Unknown error')}"
            logger.error(error_msg)
            return jsonify({"code": 500, "message": error_msg}), 500

        inventory_updates.append({
            "medication": med_name,
            "medicationID": med_id,
            "previous_quantity": current_stock,
            "new_quantity": new_quantity,
            "price": med_price
        })


    # Update prescription status
    status_response = requests.put(
        f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}/status",
        json={"status": True},
        timeout=3
    )
    
    if status_response.status_code != 200:
        error_msg = "Prescription dispensed but status update failed"
        logger.error(error_msg)
        return jsonify({"code": 500, "message": error_msg}), 500

    return jsonify({
        "code": 200,
        "message": "Prescription dispensed successfully",
        "data": {
            "prescription_id": prescription_id,
            "inventory_updates": inventory_updates
        }
    })

if __name__ == '__main__':
    logger.info("Starting Pharmacy Service")
    app.run(host='0.0.0.0', port=5004, debug=False)
