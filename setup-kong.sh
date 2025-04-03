#!/bin/bash

# Wait until Kong is up
echo "⏳ Waiting for Kong Admin API to be ready..."
until curl -s http://localhost:8001 > /dev/null; do
  sleep 1
done
echo "✅ Kong is ready!"

# Helper function to register service + route
register_service_and_route() {
  local service_name=$1
  local url=$2
  shift 2
  local paths=("$@")

  echo "🔗 Registering $service_name..."

  curl -s -X POST http://localhost:8001/services \
    --data name="$service_name" \
    --data url="$url" > /dev/null

  for path in "${paths[@]}"; do
    curl -s -X POST http://localhost:8001/services/${service_name}/routes \
      --data paths[]="$path" \
      --data strip_path=false > /dev/null
    echo "    ↳ Route added: $path"
  done
}

### Register each composite service
register_service_and_route "pharmacy-service"             "http://pharmacy:5004" \
  "/pharmacy" "/pharmacy/inventory" "/pharmacy/dispense" "/pharmacy/test/process-queue" "/pharmacy/prescription"

register_service_and_route "createprescription-service"   "http://createPrescription:6003" \
  "/create_prescription"

register_service_and_route "book-appointment-service"     "http://availability:5000" \
  "/searchDoctors" "/createAppointment"

register_service_and_route "doctormanagement-service"     "http://doctorManagement:6002" \
  "/doctor" "/doctor_management/patient_records" "/doctor_management/appointment"

# Summary
echo "✅ All services and routes registered!"


