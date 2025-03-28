from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
CORS(app)

INVENTORY_API_BASE_URL = "https://personal-dxi3ngjv.outsystemscloud.com/Inventory/rest/v1"

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
        response = requests.post(f"{INVENTORY_API_BASE_URL}/inventory", json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

@app.route("/pharmacy/inventory", methods=['PUT'])
def update_medication_quantity():
    try:
        data = request.json
        response = requests.put(f"{INVENTORY_API_BASE_URL}/inventory", json=data)
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

@app.route("/pharmacy/prescription/<prescription_id>", methods=['GET'])
def get_prescription(prescription_id):
    try:
        # Get the prescription service URL from environment variable with fallback
        prescription_service_url = os.environ.get('PRESCRIPTION_SERVICE_URL', 'http://prescription:5003')
        prescription_url = f"{prescription_service_url}/prescription/{prescription_id}"
        
        print(f"Requesting prescription from: {prescription_url}")
        
        # Add timeout to prevent hanging requests
        response = requests.get(prescription_url, timeout=5)
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        
        # Handle different HTTP status codes appropriately
        if response.status_code == 404:
            return jsonify({
                "code": 404,
                "message": f"Prescription not found for id {prescription_id}"
            }), 404
        elif response.status_code != 200:
            return jsonify({
                "code": response.status_code,
                "message": f"Prescription service returned error: {response.text}"
            }), response.status_code
        
        # Check if response has content before parsing
        if not response.content or len(response.content.strip()) == 0:
            return jsonify({
                "code": 500,
                "message": "Empty response from prescription service"
            }), 500
        
        try:
            prescription_data = response.json()
        except ValueError as json_error:
            return jsonify({
                "code": 500,
                "message": f"Invalid JSON response from prescription service: {str(json_error)}",
                "response_content": response.text
            }), 500
        
        # Add pharmacy-specific information
        prescription_data["data"]["pharmacy_info"] = {
            "processing_status": "ready_for_pickup",
            "estimated_pickup_time": "2025-03-29T10:00:00+08:00",
            "pharmacy_notes": "Please bring your ID for verification"
        }
        
        return jsonify(prescription_data), 200
    except requests.exceptions.ConnectionError:
        return jsonify({
            "code": 503,
            "message": f"Cannot connect to prescription service at {prescription_service_url}"
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "code": 504,
            "message": "Prescription service request timed out"
        }), 504
    except Exception as e:
        print(f"Exception in get_prescription: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error retrieving prescription: {str(e)}"
        }), 500




if __name__ == '__main__':
    print("Pharmacy Service is running")
    app.run(host='0.0.0.0', port=5004, debug=True)
