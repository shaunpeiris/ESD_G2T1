<p align="center">
  <img src="https://github.com/shaunpeiris/ESD_G2T1/blob/main/UI/images/MediSync_Icon.png" alt="UrbanRenew Logo" width="300" height="300">
</p>

# ESD_G2T1
MediSync is a digital health management platform can solve these problems by integrating key healthcare functions into one system. It allows patients, doctors, pharmacists to easily interact, share information, and complete tasks efficiently in a secure and scalable way.

# How to run services
Download GitHub from https://github.com/shaunpeiris/ESD_G2T1

#To run Atomic, Composite, External Services, Kong configurations
- navigate into the root directory ('/ESD_G2T1') in terminal 
- run ```docker compose up -d –build```
- run “./setup-kong.sh” (Mac) or “./setup_kong.bat”(Windows)	
 
# To access the starting page
http://localhost:8080/views	

# Account Data to test the application
Sample Doctor Login
Email: dr.steven.walker@hospital.com
Password: abc123

Change to any doctors name when you book an appointment
Email: dr.{firstname}.{lastname}@hospital.com
Password: abc123

Sample Pharmacy Login
Email: pharmacy@hospital.com
Password: abc123

Sample Patient Login
Email: emma@example.com
Password: pass123

Email: sophia@example.com
Password: pass123

# Note
- Availability, Doctor and Pharmacy services are deployed externally (deployed on Azure)
