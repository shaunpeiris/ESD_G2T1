from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import logging
from functools import lru_cache, wraps
import amqp_connection
import json
from datetime import datetime

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

def update_patient_data(patient_id, update_data):
    """
    Update patient data via the patient service
    """
    try:
        # Forward the update request to the patient service
        response = make_api_request(
            'PUT', 
            f"{PATIENT_SERVICE_URL}/patient/update/personal", 
            json={"id": patient_id, **update_data}
        )
        
        if response.status_code != 200:
            error_msg = f"Patient service error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return None, response.status_code, error_msg
        
        result = response.json()
        if result.get('code') != 200:
            error_msg = f"Patient data update failed: {result.get('message', 'Unknown error')}"
            logger.error(error_msg)
            return None, result.get('code', 500), error_msg
        
        updated_patient_data = result.get('data', {})
        return updated_patient_data, 200, "Patient data updated successfully"
    except requests.exceptions.RequestException as e:
        error_msg = f"Error connecting to patient service: {str(e)}"
        logger.error(error_msg)
        return None, 503, error_msg

# API Routes
@app.route("/pharmacy/patient/<patient_id>", methods=['GET'])
@handle_api_error
def get_patient_details(patient_id):
    """
    Get detailed patient information including contact details.
    """
    patient_data, status_code, message = get_patient_data(patient_id)
    
    if status_code != 200:
        return create_response(status_code, message)
    
    # Add contact information explicitly to ensure it's included
    enhanced_data = {
        "id": patient_data.get("id"),
        "name": patient_data.get("name"),
        "email": patient_data.get("email"),
        "mobile": patient_data.get("phone_number") or patient_data.get("mobile")
    }
    
    return create_response(200, "Patient data retrieved successfully", enhanced_data)


@app.route("/pharmacy/appointment/<appointment_id>", methods=['GET'])
@handle_api_error
def get_appointment_by_id(appointment_id):
    """
    Get appointment data by ID and return in a format compatible with the frontend.
    """
    appointment_data, status_code, message = get_appointment_data(appointment_id)
    
    if status_code != 200:
        return create_response(status_code, message)
        
    return create_response(200, "Appointment data retrieved successfully", appointment_data)

@app.route("/pharmacy/update-patient", methods=['PUT'])
@handle_api_error
def update_patient():
    data = request.json
    patient_id = data.get('id')
    
    if not patient_id:
        return create_response(400, "Patient ID is required")
    
    # Create update data with only the fields we want to update
    update_data = {
        "name": data.get('name'),
        "email": data.get('email'),
        "mobile": data.get('mobile')
    }
    
    updated_patient, status_code, message = update_patient_data(patient_id, update_data)
    
    if status_code != 200:
        return create_response(status_code, message)
    
    return create_response(200, "Patient information updated successfully", updated_patient)


@app.route("/pharmacy/prescriptions", methods=['GET'])
@handle_api_error
def get_all_prescriptions():
    try:
        # Make request to the prescription service
        response = make_api_request('GET', f"{PRESCRIPTION_SERVICE_URL}/prescription")
        if response.status_code != 200:
            logger.error(f"Failed to retrieve prescriptions: {response.text}")
            return create_response(
                response.status_code,
                f"Error retrieving prescriptions: {response.text}"
            )

        # Extract prescription data from response
        response_data = response.json()
        if not isinstance(response_data, dict):
            return create_response(500, "Invalid response format from prescription service")
        
        prescription_data = response_data.get('data', [])
        if not isinstance(prescription_data, list):
            if prescription_data:
                prescription_data = [prescription_data]
            else:
                prescription_data = []

        # Transform prescription data for frontend compatibility
        transformed_prescriptions = []
        patient_cache = {}  # Cache patient data to reduce API calls
        
        for prescription in prescription_data:
            if not isinstance(prescription, dict):
                continue
                
            appointment_id = prescription.get('appointment_id')
            patient_name = "Unknown Patient"
            
            # Use cached patient data if available
            if appointment_id and appointment_id in patient_cache:
                patient_name = patient_cache[appointment_id]
            elif appointment_id:
                try:
                    # Get appointment data with error handling
                    appointment_data, status_code, message = get_appointment_data(appointment_id)
                    
                    if status_code == 200 and appointment_data and 'patient_id' in appointment_data:
                        patient_id = appointment_data.get('patient_id')
                        
                        # Get patient data with error handling
                        patient_data, patient_status, _ = get_patient_data(patient_id)
                        
                        if patient_status == 200 and patient_data:
                            # Check various potential field names for first and last name
                            first_name = patient_data.get('first_name', 
                                        patient_data.get('firstName', 
                                            patient_data.get('given_name', 
                                            patient_data.get('givenName', ''))))
                                            
                            last_name = patient_data.get('last_name', 
                                        patient_data.get('lastName', 
                                            patient_data.get('family_name', 
                                            patient_data.get('familyName', ''))))
                            
                            # If still no name found, try name or fullName fields
                            if not first_name and not last_name:
                                full_name = patient_data.get('name', patient_data.get('fullName', ''))
                                if full_name:
                                    name_parts = full_name.split()
                                    if len(name_parts) > 1:
                                        first_name = name_parts[0]
                                        last_name = ' '.join(name_parts[1:])
                                    else:
                                        first_name = full_name
                            
                            patient_name = f"{first_name} {last_name}".strip()
                            if not patient_name:
                                patient_name = f"Patient #{patient_id}"
                                
                            # Cache this patient name for future prescriptions
                            patient_cache[appointment_id] = patient_name
                except Exception as e:
                    logger.error(f"Error retrieving patient data for appointment {appointment_id}: {str(e)}")
                    # Continue with Unknown Patient rather than fail the entire request
            
            # Determine status for UI (ensure correct status conversion)
            status_value = prescription.get('status')
            if status_value is True or (isinstance(status_value, str) and status_value.lower() == 'completed'):
                prescription_status = "completed"
            else:
                prescription_status = "pending"
            
            # Build a UI-friendly prescription object
            transformed_prescription = {
                "id": prescription.get('prescription_id'),
                "prescriptionNumber": prescription.get('prescription_id'),
                "patientName": patient_name,
                "date": prescription.get('date', datetime.now().strftime("%Y-%m-%d")),
                "medicationCount": len(prescription.get('medicine', [])) if isinstance(prescription.get('medicine', []), list) else 0,
                "status": prescription_status,
                "isUrgent": False
            }
            
            transformed_prescriptions.append(transformed_prescription)
            
        return jsonify(transformed_prescriptions), 200
        
    except Exception as e:
        logger.error(f"Error in get_all_prescriptions: {str(e)}")
        return create_response(500, f"An error occurred retrieving prescriptions: {str(e)}")


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

@app.route("/pharmacy/dispense/<prescription_id>", methods=['POST'])
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

    # Send SMS notification - UPDATED ERROR MESSAGE
    phone_number = patient_data.get('mobile') or patient_data.get('phone_number')
        
    if not phone_number:
        logger.error(f"Patient (ID: {patient_id}) has no phone number")
        return create_response(400, f"Billing failed: Patient has no valid phone number. {phone_number}")

    sms_message = f"Your prescription has been collected. Please check your email for the payment link."
    sms_sent = send_sms_notification(phone_number, sms_message)
    
    # Send email notification - UPDATED ERROR MESSAGE
    email = patient_data.get('email')
    
    if not email:
        logger.error(f"Patient (ID: {patient_id}) has no email address")
        return create_response(400, "Billing failed: Patient has no valid email address")

    email_subject = f"Prescription Payment"
    email_message = f"Your prescription has been completed. Please complete the payment at: {checkout_url}"
    email_sent = send_email_notification(email, email_subject, email_message)
    
    if not sms_sent or not email_sent:
        error_msg = "Failed to send notifications. "
        if not sms_sent:
            error_msg += "SMS notification failed. "
        if not email_sent:
            error_msg += "Email notification failed. "
        logger.error(error_msg)
        return create_response(500, f"Billing failed: {error_msg.strip()}")
    
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

def setup_prescription_queue_consumer():
    """
    Set up the AMQP consumer to listen for prescription messages.
    This should be called when the application starts.
    """
    try:
        # Create a connection (using your existing amqp_connection module)
        connection = amqp_connection.create_connection()
        channel = connection.channel()
        
        # Declare the exchange (same as in your CreatePrescription service)
        exchange_name = "dispenser_direct"
        channel.exchange_declare(exchange=exchange_name, exchange_type='direct', durable=True)
        
        # Declare a queue
        result = channel.queue_declare(queue='prescription_processing_queue', durable=True)
        queue_name = result.method.queue
        
        # Bind the queue to the exchange with the routing key
        routing_key = "prescription.id"
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
        
        # Set prefetch count to limit concurrent processing
        channel.basic_qos(prefetch_count=1)
        
        # Set up the consumer
        channel.basic_consume(queue=queue_name, on_message_callback=process_prescription_from_queue)
        
        logger.info(f"AMQP consumer set up. Waiting for prescription messages.")
        
        # Start consuming (this is a blocking call)
        channel.start_consuming()
        
    except Exception as e:
        logger.error(f"Error setting up AMQP consumer: {str(e)}")
        raise

# URLs from environment variables - same as in your pharmacy service
INVENTORY_API_BASE_URL = os.environ.get('INVENTORY_API_BASE_URL')
PRESCRIPTION_SERVICE_URL = os.environ.get('PRESCRIPTION_SERVICE_URL')
BILLING_SERVICE_URL = os.environ.get('BILLING_SERVICE_URL')
PATIENT_SERVICE_URL = os.environ.get('PATIENT_SERVICE_URL')
APPOINTMENT_SERVICE_URL = os.environ.get('APPOINTMENT_SERVICE_URL')
NOTIF_SERVICE_URL = os.environ.get('NOTIF_SERVICE_URL')

def process_prescription_from_queue(ch, method, properties, body):
    """
    Process a prescription message received from the AMQP queue.
    This function should be called by an AMQP consumer as a callback.
    """
    try:
        # Parse the message body
        message = json.loads(body)
        prescription_id = message.get('prescription_id')
        
        if not prescription_id:
            logger.error("Received message without prescription_id")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        logger.info(f"Processing prescription {prescription_id} from queue")
        
        # Get prescription data
        prescription_data, status_code, message = get_prescription_data(prescription_id)
        
        if status_code != 200:
            logger.error(f"Failed to get prescription data: {message}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        # Get appointment ID from prescription data
        appointment_id = prescription_data.get('appointment_id')
        if not appointment_id:
            logger.error("Appointment ID not found in prescription data")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Process medications from prescription
        medications = prescription_data.get('medicine', [])
        
        if not isinstance(medications, list):
            logger.error("Invalid medications format in prescription")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        # Validate all medications without updating inventory yet
        medication_updates = []
        payment_medications = []
        
        for med in medications:
            validation_result, status_code, message = validate_medication(med)
            if status_code != 200:
                logger.error(f"Medication validation failed: {message}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            medication_updates.append(validation_result)
            payment_medications.append({
                "medication": validation_result["medication"],
                "medicationID": validation_result["medicationID"],
                "price": validation_result["price"]
            })
        
        # Create billing session
        payment_success, payment_message, checkout_url = create_billing_session(
            prescription_id, 
            appointment_id,
            payment_medications
        )
        
        if not payment_success:
            logger.error(f"Billing failed: {payment_message}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Get patient data for notifications
        appointment_data, status_code, message = get_appointment_data(appointment_id)
        if status_code != 200:
            logger.error(f"Failed to get appointment data: {message}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        patient_id = appointment_data.get('patient_id')
        if not patient_id:
            logger.error("Patient ID not found in appointment data")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        patient_data, status_code, message = get_patient_data(patient_id)
        if status_code != 200:
            logger.error(f"Failed to get patient data: {message}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Send SMS notification
        phone_number = patient_data.get('mobile') or patient_data.get('phone_number')
        if not phone_number:
            logger.error(f"Patient (ID: {patient_id}) has no phone number")
            logger.error("Cannot continue with processing: Valid phone number required")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        else:
            sms_message = f"Your prescription has been processed. Please check your email for the payment link."
            sms_sent = send_sms_notification(phone_number, sms_message)
            # Add verification of SMS success
            if not sms_sent:
                logger.error(f"Failed to send SMS notification to {phone_number} for prescription {prescription_id}. Aborting inventory update.")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
        
        # Send email notification
        email = patient_data.get('email')
        if not email:
            logger.error("Patient email not found, cannot send payment link")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        email_subject = "Your Prescription Payment"
        email_message = f"Your prescription has been processed. Please complete the payment at: {checkout_url}"
        email_sent = send_email_notification(email, email_subject, email_message)
        
        if not email_sent:
            logger.error(f"Failed to send email notification to {email} for prescription {prescription_id}. Aborting inventory update.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Update inventory after successful notifications
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
                logger.error(f"Inventory update failed: {message}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            inventory_updates.append({
                "medication": update["medication"],
                "medicationID": update["medicationID"],
                "previous_quantity": update["current_stock"],
                "new_quantity": update["new_quantity"],
                "price": update["price"]
            })
        
        # Update prescription status to processed
        status_result, status_code, status_message = update_prescription_status(prescription_id, True)
        if status_code != 200:
            logger.error(f"Prescription status update failed: {status_message}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        logger.info(f"Prescription {prescription_id} successfully processed from queue")
        
        # Log the successful processing
        processing_result = {
            "prescription_id": prescription_id,
            "inventory_updates": inventory_updates,
            "payment_url": checkout_url,
            "sms_notification_sent": sms_sent,
            "email_notification_sent": email_sent
        }
        logger.info(f"Processing result: {json.dumps(processing_result)}")
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in message")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing prescription from queue: {str(e)}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

# test function
@app.route("/pharmacy/test/process-queue", methods=['POST'])
@handle_api_error
def test_process_queue():
    data = request.json
    prescription_id = data.get('prescription_id')
    
    if not prescription_id:
        return create_response(400, "prescription_id is required")
    
    # Manually create the message that would come from the queue
    ch_mock = type('obj', (object,), {
        'basic_ack': lambda delivery_tag: None
    })
    method_mock = type('obj', (object,), {
        'delivery_tag': 1
    })
    
    # Invoke the queue processor directly with the mocked objects
    process_prescription_from_queue(
        ch_mock, 
        method_mock,
        None,
        json.dumps({"prescription_id": prescription_id}).encode()
    )
    
    return create_response(200, f"Test processing of prescription {prescription_id} initiated")

import threading
if __name__ == '__main__':
    logger.info("Starting Pharmacy Service")
    # Start the AMQP consumer in a background thread
    consumer_thread = threading.Thread(target=setup_prescription_queue_consumer)
    consumer_thread.daemon = True
    consumer_thread.start()
    
    app.run(host='0.0.0.0', port=5004, debug=False)
