#!/bin/bash

echo "⏳ Waiting for Kong Admin API to be ready..."

# Wait for Kong
until curl -s http://localhost:8001 > /dev/null 2>&1; do
  sleep 1
done

echo "✅ Kong is ready!"

# Register pharmacy-service
echo "🔗 Registering pharmacy-service..."
curl -s -X POST http://localhost:8001/services --data name=pharmacy-service --data url=http://pharmacy:5004 > /dev/null
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy" --data strip_path=false > /dev/null && echo "    ↳ Route added: /pharmacy"
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy/inventory" --data strip_path=false > /dev/null && echo "    ↳ Route added: /pharmacy/inventory"
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy/dispense" --data strip_path=false > /dev/null && echo "    ↳ Route added: /pharmacy/dispense"
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy/test/process-queue" --data strip_path=false > /dev/null && echo "    ↳ Route added: /pharmacy/test/process-queue"
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy/prescription" --data strip_path=false > /dev/null && echo "    ↳ Route added: /pharmacy/prescription"

# Register createprescription-service
echo "🔗 Registering createprescription-service..."
curl -s -X POST http://localhost:8001/services --data name=createprescription-service --data url=http://createPrescription:6003 > /dev/null
curl -s -X POST http://localhost:8001/services/createprescription-service/routes --data "paths[]=/create_prescription" --data strip_path=false > /dev/null && echo "    ↳ Route added: /create_prescription"

# Register book-appointment-service
echo "🔗 Registering book-appointment-service..."
curl -s -X POST http://localhost:8001/services --data name=book-appointment-service --data url=http://bookAppointment:5000 > /dev/null
curl -s -X POST http://localhost:8001/services/book-appointment-service/routes --data "paths[]=/searchDoctors" --data strip_path=false > /dev/null && echo "    ↳ Route added: /searchDoctors"
curl -s -X POST http://localhost:8001/services/book-appointment-service/routes --data "paths[]=/createAppointment" --data strip_path=false > /dev/null && echo "    ↳ Route added: /createAppointment"

# Register doctormanagement-service
echo "🔗 Registering doctormanagement-service..."
curl -s -X POST http://localhost:8001/services --data name=doctormanagement-service --data url=http://doctorManagement:6002 > /dev/null
curl -s -X POST http://localhost:8001/services/doctormanagement-service/routes --data "paths[]=/doctor" --data strip_path=false > /dev/null && echo "    ↳ Route added: /doctor"
curl -s -X POST http://localhost:8001/services/doctormanagement-service/routes --data "paths[]=/doctor_management/patient_records" --data strip_path=false > /dev/null && echo "    ↳ Route added: /doctor_management/patient_records"
curl -s -X POST http://localhost:8001/services/doctormanagement-service/routes --data "paths[]=/doctor_management/appointment" --data strip_path=false > /dev/null && echo "    ↳ Route added: /doctor_management/appointment"
curl -s -X POST http://localhost:8001/services/doctormanagement-service/routes --data "paths[]=/get_prescription" --data strip_path=false > /dev/null && echo "    ↳ Route added: /get_prescription"

# Register appointment-service
echo "🔗 Registering appointment-service..."
curl -s -X POST http://localhost:8001/services --data name=appointment-service --data url=http://appointment:5002 > /dev/null
curl -s -X POST http://localhost:8001/services/appointment-service/routes --data "paths[]=/appointment/patient" --data strip_path=false > /dev/null && echo "    ↳ Route added: /appointment"

# Register hospital-service (external IP)
echo "🔗 Registering hospital-service (external)..."
curl -s -X POST http://localhost:8001/services --data name=hospital-service --data url=http://104.214.186.4:5010 > /dev/null
curl -s -X POST http://localhost:8001/services/hospital-service/routes --data "paths[]=/specializations" --data strip_path=false > /dev/null && echo "    ↳ Route added: /specializations"
curl -s -X POST http://localhost:8001/services/hospital-service/routes --data "paths[]=/polyclinics" --data strip_path=false > /dev/null && echo "    ↳ Route added: /polyclinics"
curl -s -X POST http://localhost:8001/services/hospital-service/routes --data "paths[]=/doctors" --data strip_path=false > /dev/null && echo "    ↳ Route added: /doctors"

echo "✅ All services and routes registered!"



