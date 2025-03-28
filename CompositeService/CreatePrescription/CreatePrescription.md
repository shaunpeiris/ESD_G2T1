### Create prescription microservice 

*Details*

port 6003

*instructions*

```/create_prescription```
1. method:POST 
- details:
    1. retrieve presciption submitted by doctor through UI  
    2. get patient allergy 
    3. send to prescription simple service to check for allergy against prescription
    4. if allergic, will send back to UI to show doctor
    5. if not it will be inserted into the DB 
    6. Send the prescription ID to AMQP to forward to processprescription microservice

*Version*
v1.0
created the new complex service



