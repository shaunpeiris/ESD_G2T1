from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import logging
from functools import lru_cache, wraps

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
INVENTORY_API_BASE_URL = os.environ.get('INVENTORY_API_BASE_URL')
PRESCRIPTION_SERVICE_URL = os.environ.get('PRESCRIPTION_SERVICE_URL')
BILLING_SERVICE_URL = os.environ.get('BILLING_SERVICE_URL')
PATIENT_SERVICE_URL = os.environ.get('PATIENT_SERVICE_URL')
APPOINTMENT_SERVICE_URL = os.environ.get('APPOINTMENT_SERVICE_URL')
NOTIF_SERVICE_URL = os.environ.get('NOTIF_SERVICE_URL')

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

# Inventory management functions
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

def validate_medication(med):
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

# Prescription management functions
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

# Appointment and patient functions
def get_appointment_data(appointment_id):
    try:
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
    try:
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

# Billing function
def create_billing_session(prescription_id, appointment_id, medications):
    try:
        # Get appointment data to retrieve patient ID
        appointment_data, status_code, message = get_appointment_data(appointment_id)
        
        if status_code != 200:
            logger.error(f"Failed to get appointment data: {message}")
            return False, f"Failed to get appointment data: {message}", None
        
        # Extract patient ID from appointment data
        patient_id = appointment_data.get('patient_id')
        if not patient_id:
            logger.error(f"Patient ID not found in appointment data for appointment {appointment_id}")
            return False, f"Patient ID not found in appointment data for appointment {appointment_id}", None
        
        logger.info(f"Retrieved patient ID {patient_id} from appointment {appointment_id}")
        
        # Get patient details using the patient ID
        patient_data, status_code, message = get_patient_data(patient_id)
        
        if status_code != 200:
            logger.error(f"Failed to get patient data for ID {patient_id}: {message}")
            return False, f"Failed to get patient data: {message}", None
        
        # Extract patient email
        patient_email = patient_data.get('email')
        if not patient_email:
            logger.error(f"Email not found for patient {patient_id}")
            return False, f"Patient email not found for patient {patient_id}", None
        
        logger.info(f"Retrieved email for patient {patient_id}")
        
        # Prepare request data for billing service
        billing_data = {
            "prescription_id": prescription_id,
            "patient_id": patient_id,
            "patient_email": patient_email,
            "medicines": medications
        }
        
        # Call the billing service
        try:
            response = requests.post(
                f"{BILLING_SERVICE_URL}/create-checkout-session",
                json=billing_data,
                timeout=5
            )
            
            # Handle billing service response
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

# Notification functions
def send_sms_notification(phone_number, message):
    payload = {
        "method": "sms",
        "recipient": phone_number,
        "message": message
    }
    try:
        response = requests.post(f"{NOTIF_SERVICE_URL}/notify", json=payload, timeout=5)
        if response.status_code == 201:
            logger.info(f"SMS notification sent successfully to {phone_number}")
            return True
        else:
            logger.error(f"Failed to send SMS notification: Status code {response.status_code}, Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error while sending SMS notification to {phone_number}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while sending SMS notification to {phone_number}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending SMS notification to {phone_number}: {str(e)}")
        return False

def send_email_notification(email, subject, message):
    payload = {
        "method": "email",
        "recipient": email,
        "subject": subject,
        "message": message
    }
    try:
        response = requests.post(f"{NOTIF_SERVICE_URL}/notify", json=payload, timeout=5)
        if response.status_code == 201:
            logger.info(f"Email notification sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send email notification: Status code {response.status_code}, Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error while sending email notification to {email}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while sending email notification to {email}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email notification to {email}: {str(e)}")
        return False

# API Routes
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
    prescription_data, status_code, message = get_prescription_data(prescription_id)
    
    if status_code != 200:
        return create_response(404, f"Prescription {prescription_id} not found")

    if prescription_data.get('status', False):
        return create_response(400, f"Prescription {prescription_id} has already been dispensed")
    
    medications = prescription_data.get('medicine', [])
    
    if not isinstance(medications, list):
        return create_response(400, "Invalid medications format in prescription")

    # Validate all medications without updating inventory
    medication_updates = []
    payment_medications = []
    
    for med in medications:
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
    
    appointment_data, status_code, message = get_appointment_data(appointment_id)
    if status_code != 200:
        return create_response(400, f"Failed to get appointment data: {message}")

    patient_id = appointment_data.get('patient_id')
    if not patient_id:
        return create_response(400, "Patient ID not found in appointment data")

    patient_data, status_code, message = get_patient_data(patient_id)
    if status_code != 200:
        return create_response(400, f"Failed to get patient data: {message}")

    # Send SMS notification
    test_phone_number = "+6598345858"  # For testing purposes
    phone_number = test_phone_number if test_phone_number else patient_data.get('phone_number')
    
    if not phone_number:
        return create_response(400, "Patient phone number not found")

    sms_message = f"Your prescription has been collected. Please check your email for the payment link. Thanks for coming la see u again have a nice day :)"
    sms_sent = send_sms_notification(phone_number, sms_message)
    
    # Send email notification
    test_email = "kesterfun@live.com"  # For testing purposes
    email = test_email if test_email else patient_data.get('email')
    
    if not email:
        return create_response(400, "Patient email not found")

    email_subject = f"Pay up"
    email_message = f"Your prescription has been completed. Please complete the payment at: {checkout_url}"
    email_sent = send_email_notification(email, email_subject, email_message)
    
    if not sms_sent or not email_sent:
        logger.error("Failed to send notifications")
        return create_response(500, "Failed to send notifications. Prescription not dispensed.")
    
    # Only update inventory AFTER successful billing URL generation and notifications
    inventory_updates = []
    for update in medication_updates:
        med_update_data = {
            "medicationID": update["medicationID"],
            "medicationName": update["medication"],
            "quantity": update["new_quantity"],
            "price": update["price"]
        }
        
        result, status_code, message = update_inventory(med_update_data)
        if status_code != 200:
            logger.error(f"Inventory update failed after successful billing and notifications: {message}")
            return create_response(500, f"Billing and notifications successful but inventory update failed: {message}")
            
        inventory_updates.append({
            "medication": update["medication"],
            "medicationID": update["medicationID"],
            "previous_quantity": update["current_stock"],
            "new_quantity": update["new_quantity"],
            "price": update["price"]
        })
    
    # Update prescription status after successful billing, notifications, and inventory updates
    status_result, status_code, status_message = update_prescription_status(prescription_id, True)
    if status_code != 200:
        logger.error(f"Prescription status update failed: {status_message}")
        return create_response(500, f"Billing, notifications, and inventory updated, but status update failed: {status_message}")
    
    response_data = {
        "prescription_id": prescription_id,
        "inventory_updates": inventory_updates,
        "payment_url": checkout_url,
        "sms_notification_sent": sms_sent,
        "email_notification_sent": email_sent
    }
    
    logger.info(f"Prescription {prescription_id} successfully billed, notified, and dispensed")
    return create_response(200, "Prescription billed, notified, and dispensed successfully", response_data)

if __name__ == '__main__':
    logger.info("Starting Pharmacy Service")
    app.run(host='0.0.0.0', port=5004, debug=False)