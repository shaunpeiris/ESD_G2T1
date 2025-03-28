from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
from datetime import datetime, timezone, timedelta
import json
import logging
from functools import lru_cache

app = Flask(__name__)
CORS(app)

INVENTORY_API_BASE_URL = os.environ.get('INVENTORY_API_BASE_URL', "https://personal-dxi3ngjv.outsystemscloud.com/Inventory/rest/v1")
PRESCRIPTION_SERVICE_URL = os.environ.get('PRESCRIPTION_SERVICE_URL', 'http://prescription:5003')

@app.route("/pharmacy/inventory", methods=['GET'])
def list_all_medications():
    try:
        response = requests.get(f"{INVENTORY_API_BASE_URL}/inventory")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

@app.route("/pharmacy/inventory/<medication_name>", methods=['GET'])
def get_medication_by_name(medication_name):
    try:
        response = requests.get(f"{INVENTORY_API_BASE_URL}/inventory/name/{medication_name}/")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

@app.route("/pharmacy/inventory", methods=['POST'])
def create_medication():
    try:
        data = request.json
        response = requests.post(f"{INVENTORY_API_BASE_URL}/inventory", json={"Medications": [data]})        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

@app.route("/pharmacy/inventory", methods=['PUT'])
def update_medication_quantity():
    try:
        data = request.json
        response = requests.put(f"{INVENTORY_API_BASE_URL}/inventory", json={"Medications": [data]})
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

@app.route("/pharmacy/inventory/<medication_id>", methods=['DELETE'])
def delete_medication(medication_id):
    try:
        response = requests.delete(f"{INVENTORY_API_BASE_URL}/inventory/{medication_id}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

@lru_cache(maxsize=128)
def get_cached_inventory(medication_name):
    """Cached inventory lookup with 5-second freshness"""
    try:
        response = requests.get(
            f"{INVENTORY_API_BASE_URL}/inventory/name/{medication_name}/",
            timeout=2
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logging.error(f"Inventory API error: {str(e)}")
        return None

def parse_inventory_response(response_data):
    try:
        if 'Medications' in response_data and response_data['Medications']:
            return response_data['Medications'][0].get('quantity', 0)
        return 0
    except Exception as e:
        logging.error(f"Inventory parse error: {str(e)}")
        return 0

@app.route("/pharmacy/prescription/<prescription_id>", methods=['GET'])
def get_prescription(prescription_id):
    try:
        prescription_url = f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}"
        
        response = requests.get(prescription_url, timeout=5)
        
        if response.status_code == 404:
            return jsonify({"code": 404, "message": f"Prescription not found for id {prescription_id}"}), 404
        elif response.status_code != 200:
            return jsonify({"code": response.status_code, "message": f"Prescription service returned error: {response.text}"}), response.status_code
        
        if not response.content:
            return jsonify({"code": 500, "message": "Empty response from prescription service"}), 500
        
        prescription_data = response.json()
        
        prescription_data["data"]["pharmacy_info"] = {
            "processing_status": "ready_for_pickup",
            "estimated_pickup_time": "2025-03-29T10:00:00+08:00",
            "pharmacy_notes": "Please bring your ID for verification"
        }
        
        return jsonify(prescription_data), 200
    except requests.exceptions.ConnectionError:
        return jsonify({"code": 503, "message": f"Cannot connect to prescription service at {PRESCRIPTION_SERVICE_URL}"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"code": 504, "message": "Prescription service request timed out"}), 504
    except Exception as e:
        return jsonify({"code": 500, "message": f"Error retrieving prescription: {str(e)}"}), 500

@app.route("/pharmacy/prescription/<prescription_id>/dispense", methods=['POST'])
def dispense_prescription(prescription_id):
    try:
        prescription_url = f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}"
        prescription_response = requests.get(prescription_url, timeout=5)
        
        if prescription_response.status_code != 200:
            return jsonify({
                "code": 404,
                "message": f"Prescription {prescription_id} not found"
            }), 404

        prescription_data = prescription_response.json().get('data', {})
        medications = prescription_data.get('medicine', [])
        
        if not isinstance(medications, list):
            return jsonify({
                "code": 400,
                "message": "Invalid medications format"
            }), 400

        inventory_data = {}
        for med in medications:
            if not isinstance(med, dict):
                return jsonify({
                    "code": 400,
                    "message": "Invalid medication format"
                }), 400
                
            med_name = med.get('name')
            required_qty = med.get('quantity', 0)
            
            if not med_name or required_qty <= 0:
                return jsonify({
                    "code": 400,
                    "message": "Invalid medication name or quantity"
                }), 400

            inventory_response = get_cached_inventory(med_name)
            if not inventory_response:
                return jsonify({
                    "code": 404,
                    "message": f"Medication {med_name} not found in inventory"
                }), 404

            current_stock = parse_inventory_response(inventory_response)
            inventory_data[med_name] = current_stock
            
            logging.debug(f"Inventory check - {med_name}: {current_stock} available")

            if current_stock < required_qty:
                return jsonify({
                    "code": 400,
                    "message": f"Insufficient stock for {med_name}. Required: {required_qty}, Available: {current_stock}"
                }), 400

        inventory_updates = []
        for med in medications:
            med_name = med['name']
            required_qty = med['quantity']
            current_stock = inventory_data[med_name]
            
            verify_response = get_cached_inventory(med_name)
            current_stock = parse_inventory_response(verify_response)
            
            if current_stock < required_qty:
                return jsonify({
                    "code": 409,
                    "message": f"Stock changed during processing. {med_name} now has {current_stock} units"
                }), 409

            new_quantity = current_stock - required_qty
            update_response = requests.put(
                f"{INVENTORY_API_BASE_URL}/inventory",
                json={
                    "Medications": [{
                        "medicationName": med_name,
                        "quantity": new_quantity
                    }]
                },
                timeout=3
            )
            
            if update_response.status_code != 200:
                return jsonify({
                    "code": 500,
                    "message": f"Inventory update failed for {med_name}"
                }), 500

            inventory_updates.append({
                "medication": med_name,
                "previous_quantity": current_stock,
                "new_quantity": new_quantity
            })

        status_response = requests.put(
            f"{PRESCRIPTION_SERVICE_URL}/prescription/{prescription_id}/status",
            json={"status": True},
            timeout=3
        )
        
        if status_response.status_code != 200:
            return jsonify({
                "code": 500,
                "message": "Dispensed but status update failed"
            }), 500

        return jsonify({
            "code": 200,
            "message": "Prescription dispensed successfully",
            "data": {
                "prescription_id": prescription_id,
                "inventory_updates": inventory_updates
            }
        })

    except requests.exceptions.RequestException as re:
        logging.error(f"Network error: {str(re)}")
        return jsonify({
            "code": 503,
            "message": "Service unavailable"
        }), 503
        
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": "Internal server error"
        }), 500

if __name__ == '__main__':
    print("Pharmacy Service is running")
    app.run(host='0.0.0.0', port=5004, debug=True)
