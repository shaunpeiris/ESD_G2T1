from flask import Flask, request, jsonify
from flask_cors import CORS
# import amqp_connection
import os, sys
# import threading
import json
# import time

from invokes import invoke_http

app = Flask(__name__)
CORS(app)

# URLs for microservices
prescription_URL = "http://host.docker.internal:5003/prescription"
inventory_URL = "https://personal-dxi3ngjv.outsystemscloud.com/Inventory/rest/v1/inventory"

# Process a prescription manually via HTTP
@app.route("/process", methods=["POST"])
def process_prescription_http():
    if request.is_json:
        try:
            data = request.get_json()
            print("\nReceived a prescription ID in JSON:", data)

            # Extract prescription ID
            prescription_id = data.get("id")
            if not prescription_id:
                return jsonify({
                    "code": 400,
                    "message": "Missing prescription ID"
                }), 400

            # Process the prescription with error handling around the entire call
            try:
                result = processPrescription(prescription_id)
                # Make sure result has a 'code' key
                if isinstance(result, dict) and "code" in result:
                    return jsonify(result), result["code"]
                else:
                    print("Warning: processPrescription returned invalid result:", result)
                    return jsonify({
                        "code": 500,
                        "message": "Invalid result format from processPrescription"
                    }), 500
            except Exception as e:
                # Catch any errors from processPrescription
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
                print("Error in processPrescription:", ex_str)
                return jsonify({
                    "code": 500,
                    "message": "Error in processPrescription: " + ex_str
                }), 500
        
        except Exception as e:
            # Unexpected error in code
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "process.py internal error: " + ex_str
            }), 500
    
    # If reached here, not a JSON request
    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400

def processPrescription(id):
    # 1. Get prescription info
    # Invoke the prescription microservice
    print('\n-----Invoking prescription microservice-----')
    prescription_result = invoke_http(prescription_URL + "/" + str(id))
    print('prescription_result:', prescription_result)
    
    if prescription_result.get("code", 0) != 200:
        return {
            "code": 404,
            "message": f"Prescription not found: {id}"
        }
    
    # 2. Extract medications from the JSON medicine field
    try:
        # Get the medicine data
        medicine_data = prescription_result["data"]["medicine"]
        
        # Determine if it's already a list or needs conversion
        if isinstance(medicine_data, str):
            try:
                medicine_data = json.loads(medicine_data)
            except json.JSONDecodeError as e:
                print(f"Error decoding medicine data: {e}")
                return {
                    "code": 500,
                    "message": f"Invalid medicine data format: {str(e)}"
                }
            
        # If medicine_data is already a list (which appears to be the case)
        if isinstance(medicine_data, list):
            medications = medicine_data
        elif isinstance(medicine_data, dict):
            # If it's a dictionary with a medications field
            if "medications" in medicine_data:
                medications = medicine_data["medications"]
            else:
                # If it's a single medication object
                medications = [medicine_data]
        else:
            return {
                "code": 500,
                "message": f"Unexpected medicine data type: {type(medicine_data)}"
            }
            
        print(f"Found {len(medications)} medications in prescription")
        
    except Exception as e:
        return {
            "code": 500,
            "message": f"Error parsing prescription data: {str(e)}"
        }
    
    # Track processed medications
    processed_medications = []
    
    # 3. Process each medication
    for medication in medications:
        if not isinstance(medication, dict):
            print(f"Warning: Medication is not a dictionary: {medication}")
            continue
            
        try:
            # Get medicineID using direct access, not .get()
            medication_id = None
            if "medicineID" in medication:
                medication_id = medication["medicineID"]
            elif "medicationID" in medication:
                medication_id = medication["medicationID"]
                
            if not medication_id:
                print(f"Warning: Missing medication ID in {medication}")
                continue
                
            # Get quantity using direct access
            prescription_quantity = 1  # Default
            if "quantity" in medication:
                prescription_quantity = medication["quantity"]
            
            print(f'\n-----Invoking inventory microservice for medicine ID {medication_id}-----')

            # Get all medications and filter for the one we need
            inventory_url = f"{inventory_URL}"  # No ID in path
            get_inventory_result = invoke_http(inventory_url, method='GET')
            print('Retrieved inventory info:', get_inventory_result)

            # Process inventory result
            if "Result" not in get_inventory_result or not get_inventory_result["Result"].get("success", False):
                error_msg = get_inventory_result.get("Result", {}).get("errorMessage", "Unknown error")
                print(f"Error retrieving inventory: {error_msg}")
                continue
                
            # Find our medication in the list
            found_medication = None
            if "Medications" in get_inventory_result and get_inventory_result["Medications"]:
                for med in get_inventory_result["Medications"]:
                    if med.get("medicationID") == medication_id:
                        found_medication = med
                        break
                
            if not found_medication:
                print(f"Medication with ID {medication_id} not found in inventory")
                continue
                
            current_quantity = found_medication["quantity"]
            
            if current_quantity < prescription_quantity:
                print(f"Warning: Insufficient inventory. Needed: {prescription_quantity}, Available: {current_quantity}")
                continue
                
            new_quantity = current_quantity - prescription_quantity

            # Prepare update data
            update_inventory_data = {
                "medicationID": medication_id,
                "medicationName": found_medication["medicationName"],
                "quantity": new_quantity
            }
            
            if "price" in found_medication:
                update_inventory_data["price"] = found_medication["price"]
            
            # Update inventory - use PUT without ID in path
            update_inventory_result = invoke_http(inventory_url, method="PUT", json=update_inventory_data)
            print('Updated inventory quantity:', update_inventory_result)
            
            # Track processed medication
            medication_name = "Unknown"
            if "name" in medication:
                medication_name = medication["name"]
            elif "medicationName" in found_medication:
                medication_name = found_medication["medicationName"]
                
            processed_medications.append({
                "id": medication_id,
                "name": medication_name,
                "quantity": prescription_quantity
            })
            
        except Exception as e:
            print(f"Error processing medication: {str(e)}")
    
    # 5. Update prescription status
    try:
        update_prescription_data = {"status": True}
        update_prescription_result = invoke_http(f"{prescription_URL}/{id}/status", method="PUT", json=update_prescription_data)
        print('Successfully processed prescription:', update_prescription_result)
    except Exception as e:
        print(f"Error updating prescription status: {str(e)}")
        # Continue anyway to return what we've processed

    # Make sure to include a 'code' key in the result
    return {
        "code": 201,  # This must be present for the HTTP function to work!
        "data": {
            "processed_medications": processed_medications
        },
        "message": f"Successfully processed {len(processed_medications)} medications"
    }

# # Function to start listening to RabbitMQ for prescription IDs
# def start_listening():
#     print("Starting RabbitMQ listener...")
    
#     # Use a retry pattern to handle connection issues
#     max_retries = 5
#     for attempt in range(max_retries):
#         try:
#             # Create a new connection for the listener
#             connection = amqp_connection.create_connection()
#             print("RabbitMQ connection established")
            
#             # Create a channel
#             channel = connection.channel()
#             print("RabbitMQ channel created")
            
#             # Declare the exchange
#             exchangename = "dispenser_direct"
#             channel.exchange_declare(exchange=exchangename, exchange_type='direct', durable=True)
#             print(f"Exchange '{exchangename}' declared")
            
#             # Declare the queue
#             queue_name = "Dispenser_Queue"
#             queue_declare_result = channel.queue_declare(queue=queue_name, durable=True)
#             print(f"Queue '{queue_name}' declared, message count: {queue_declare_result.method.message_count}")
            
#             # Bind the queue to the exchange with the routing key
#             routing_key = "prescription.id"
#             channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key=routing_key)
#             print(f"Queue bound to exchange with routing key '{routing_key}'")
            
#             # Set up a callback function to handle messages
#             def callback(ch, method, properties, body):
#                 print(f"[x] Received message with delivery tag: {method.delivery_tag}")
#                 try:
#                     # Decode the message body and log it exactly as received
#                     message_body = body.decode('utf-8')
#                     print(f"Raw message body: {message_body}")
                    
#                     # Parse the JSON message
#                     message = json.loads(message_body)
#                     print(f"Parsed message: {message}")
                    
#                     # Try to extract prescription_id regardless of case
#                     prescription_id = None
#                     for key in message:
#                         if key.lower() == 'prescription_id':
#                             prescription_id = message[key]
#                             break
                    
#                     print(f"Extracted prescription_id: {prescription_id}")
                    
#                     if prescription_id:
#                         print(f"Processing prescription ID: {prescription_id}")
#                         # Process the prescription
#                         result = processPrescription(prescription_id)
#                         print(f"Processing result: {result}")
                        
#                         # Always acknowledge the message to remove it from the queue
#                         print(f"Acknowledging message with delivery tag: {method.delivery_tag}")
#                         ch.basic_ack(delivery_tag=method.delivery_tag)
#                         print("Message acknowledged successfully")
#                     else:
#                         print(f"Invalid message format, couldn't find prescription_id: {message}")
#                         # Reject the message without requeuing since it's invalid
#                         ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
#                         print("Message rejected without requeuing")
                
#                 except json.JSONDecodeError as e:
#                     print(f"Error decoding JSON message: {e}")
#                     # Reject the message without requeuing since it's invalid
#                     ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
#                     print("Invalid JSON message rejected without requeuing")
                    
#                 except Exception as e:
#                     print(f"Error processing message: {str(e)}")
#                     # Reject but don't requeue after max retries
#                     # This prevents infinite retry loops
#                     ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
#                     print("Message rejected due to processing error")
            
#             # Set up the consumer with manual ack mode
#             channel.basic_qos(prefetch_count=1)
#             channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
            
#             print(' [*] Waiting for prescription IDs. To exit press CTRL+C')
#             # Start consuming in a non-blocking way
#             try:
#                 channel.start_consuming()
#             except KeyboardInterrupt:
#                 channel.stop_consuming()
#                 connection.close()
#                 print("RabbitMQ listener stopped")
            
#             # If we get here without exception, break out of the retry loop
#             break
            
#         except Exception as e:
#             print(f"Error in RabbitMQ listener (attempt {attempt+1}/{max_retries}): {str(e)}")
#             if attempt < max_retries - 1:
#                 # Wait before retrying
#                 time.sleep(5)
#             else:
#                 print("Maximum retries reached. RabbitMQ listener failed to start.")
#                 # Continue with the Flask app even if the listener fails
#                 break

# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for processing prescriptions...")
    
    # Give time for RabbitMQ to fully initialize before connecting
    # time.sleep(5)
    
    # # Start the RabbitMQ listener in a separate thread
    # try:
    #     print("Starting RabbitMQ listener thread...")
    #     listener_thread = threading.Thread(target=start_listening)
    #     listener_thread.daemon = True  # Thread will exit when main thread exits
    #     listener_thread.start()
    #     print("RabbitMQ listener thread started successfully")
        
    #     # Give the thread a moment to start up and report any immediate errors
    #     time.sleep(2)
    #     if not listener_thread.is_alive():
    #         print("WARNING: RabbitMQ listener thread stopped unexpectedly")
    #     else:
    #         print("RabbitMQ listener thread is running")
    # except Exception as e:
    #     print(f"Error starting RabbitMQ listener thread: {str(e)}")
    
    # Start the Flask app
    app.run(host="0.0.0.0", port=5100, debug=True)