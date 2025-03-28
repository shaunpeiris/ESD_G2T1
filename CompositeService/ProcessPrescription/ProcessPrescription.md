### ProcessPrescription microservice 

*Details*

*instructions*

```/process```
1. method: POST 
- details:
    1. receive prescription id (json)
    2. get prescription record from Prescription MS
        - get quantity
        - prescriptions
    3. for each prescription:
        - update inventory quantity
        - get prescription price
        - calculate total price
    4. create invoice request
    5. return status

Microservices to start:
1. Inventory
2. Prescription
3. Invoice



