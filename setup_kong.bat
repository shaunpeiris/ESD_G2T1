@echo off
echo ⏳ Waiting for Kong Admin API to be ready...

:wait_for_kong
curl -s http://localhost:8001 >nul 2>&1
if errorlevel 1 (
    timeout /t 1 >nul
    goto wait_for_kong
)
echo ✅ Kong is ready!

REM Register pharmacy-service
echo 🔗 Registering pharmacy-service...
curl -s -X POST http://localhost:8001/services --data name=pharmacy-service --data url=http://pharmacy:5004 >nul

curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy" --data strip_path=false >nul
echo     ↳ Route added: /pharmacy
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy/inventory" --data strip_path=false >nul
echo     ↳ Route added: /pharmacy/inventory
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy/dispense" --data strip_path=false >nul
echo     ↳ Route added: /pharmacy/dispense
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy/test/process-queue" --data strip_path=false >nul
echo     ↳ Route added: /pharmacy/test/process-queue
curl -s -X POST http://localhost:8001/services/pharmacy-service/routes --data "paths[]=/pharmacy/prescription" --data strip_path=false >nul
echo     ↳ Route added: /pharmacy/prescription

REM Register createprescription-service
echo 🔗 Registering createprescription-service...
curl -s -X POST http://localhost:8001/services --data name=createprescription-service --data url=http://createPrescription:6003 >nul
curl -s -X POST http://localhost:8001/services/createprescription-service/routes --data "paths[]=/create_prescription" --data strip_path=false >nul
echo     ↳ Route added: /create_prescription

REM Register book-appointment-service
echo 🔗 Registering book-appointment-service...
curl -s -X POST http://localhost:8001/services --data name=book-appointment-service --data url=http://bookAppointment:5000 >nul
curl -s -X POST http://localhost:8001/services/book-appointment-service/routes --data "paths[]=/searchDoctors" --data strip_path=false >nul
echo     ↳ Route added: /searchDoctors
curl -s -X POST http://localhost:8001/services/book-appointment-service/routes --data "paths[]=/createAppointment" --data strip_path=false >nul
echo     ↳ Route added: /createAppointment

REM Register doctormanagement-service
echo 🔗 Registering doctormanagement-service...
curl -s -X POST http://localhost:8001/services --data name=doctormanagement-service --data url=http://doctorManagement:6002 >nul
curl -s -X POST http://localhost:8001/services/doctormanagement-service/routes --data "paths[]=/doctor" --data strip_path=false >nul
echo     ↳ Route added: /doctor
curl -s -X POST http://localhost:8001/services/doctormanagement-service/routes --data "paths[]=/doctor_management/patient_records" --data strip_path=false >nul
echo     ↳ Route added: /doctor_management/patient_records
curl -s -X POST http://localhost:8001/services/doctormanagement-service/routes --data "paths[]=/doctor_management/appointment" --data strip_path=false >nul
echo     ↳ Route added: /doctor_management/appointment

REM Register appointment-service
echo 🔗 Registering appointment-service...
curl -s -X POST http://localhost:8001/services --data name=appointment-service --data url=http://appointment:5002 >nul
curl -s -X POST http://localhost:8001/services/appointment-service/routes --data "paths[]=/appointment/patient" --data strip_path=false >nul
echo     ↳ Route added: /appointment

REM Register specializations service (external IP)
echo 🔗 Registering hospital service...
curl -s -X POST http://localhost:8001/services --data name=hospital-service --data url=http://104.214.186.4:5010 >nul
curl -s -X POST http://localhost:8001/services/hospital-service/routes --data "paths[]=/specializations" --data strip_path=false >nul
curl -s -X POST http://localhost:8001/services/hospital-service/routes --data "paths[]=/polyclinics" --data strip_path=false >nul
curl -s -X POST http://localhost:8001/services/hospital-service/routes --data "paths[]=/doctors" --data strip_path=false >nul
echo     ↳ Route added: /hospital

echo ✅ All services and routes registered!
