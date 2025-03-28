from flask import Flask, request, jsonify, render_template
import stripe
from flask_sqlalchemy import SQLAlchemy
import requests
from os import environ
import os

app = Flask(__name__, template_folder="templates")

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] =  environ.get('dbURL') 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}



db = SQLAlchemy(app)

# Stripe Configuration
STRIPE_SECRET_KEY = environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = environ.get("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = environ.get("STRIPE_WEBHOOK_SECRET")
stripe.api_key = STRIPE_SECRET_KEY


# Microservice & domain config
YOUR_DOMAIN = environ.get("YOUR_DOMAIN")
PATIENT_MICROSERVICE_URL = environ.get("PATIENT_MICROSERVICE_URL")

print(f"STRIPE_SECRET_KEY: {STRIPE_SECRET_KEY}")
print(f"STRIPE_PUBLISHABLE_KEY: {STRIPE_PUBLISHABLE_KEY}")
print(f"STRIPE_WEBHOOK_SECRET: {STRIPE_WEBHOOK_SECRET}")
print(f"YOUR_DOMAIN: {YOUR_DOMAIN}")
print(f"PATIENT_MICROSERVICE_URL: {PATIENT_MICROSERVICE_URL}")

# Dummy Prescription Data
DUMMY_PRESCRIPTION = {
    "prescription_id": 1001,
    "medicines": [
        {"name": "Paracetamol", "price": 1000},
        {"name": "Ibuprofen", "price": 2000}
    ]
}

# Define Payment Model
class Payment(db.Model):
    __tablename__ = 'payment'
    
    paymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prescriptionID = db.Column(db.Integer, nullable=False)
    patientID = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float(precision=2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def json(self):
        return {
            "paymentID": self.paymentID,
            "prescriptionID": self.prescriptionID,
            "amount": self.amount,
            "status": self.status,
            "createdAt": self.createdAt
        }

# Render Home Page
@app.route("/")
def home():
    return render_template("index.html", stripe_publishable_key=STRIPE_PUBLISHABLE_KEY, patient_url=PATIENT_MICROSERVICE_URL)

# Success Page
@app.route("/success")
def success():
    payment = Payment.query.order_by(Payment.createdAt.desc()).first()
    if payment:
        payment.status = "completed"
        db.session.commit()
    return render_template("success.html")

# Cancel Page
@app.route("/cancel")
def cancel():
    payment = Payment.query.order_by(Payment.createdAt.desc()).first()
    if payment:
        payment.status = "canceled"
        db.session.commit()
    return render_template("cancel.html")

# Error Page
@app.route("/error")
def error():
    payment = Payment.query.order_by(Payment.createdAt.desc()).first()
    if payment:
        payment.status = "failed"
        db.session.commit()
    return render_template("error.html")

# Create a Stripe Checkout Session
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        # Get data from request body
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract required patient information from request
        patient_id = request_data.get('patient_id')
        patient_email = request_data.get('patient_email')
        
        # Extract prescription information
        prescription_id = request_data.get('prescription_id')
        medicines = request_data.get('medicines', [])
        
        # Validate required fields
        if not patient_id or not patient_email or not prescription_id or not medicines:
            return jsonify({
                "error": "Missing required fields. Need patient_id, patient_email, prescription_id, and medicines"
            }), 400
        
        # Calculate total cost
        consultation_fee = 2000  # cents
        total_price = sum(m.get("price", 0) for m in medicines) + consultation_fee
        
        # Log the received data
        print(f"Processing payment for patient ID: {patient_id}, prescription ID: {prescription_id}")
        print(f"Medicines: {medicines}")
        print(f"Total price: {total_price} cents")
        
        # Save payment record
        new_payment = Payment(
            prescriptionID=prescription_id,
            patientID=patient_id,
            amount=total_price / 100,
            status="pending"
        )
        db.session.add(new_payment)
        db.session.commit()
        
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card", "paynow"],
            line_items=[{
                "price_data": {
                    "currency": "sgd",
                    "product_data": {"name": "Doctor Consultation & Medicines"},
                    "unit_amount": int(total_price),
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=patient_email,
            success_url=f"{YOUR_DOMAIN}/success",
            cancel_url=f"{YOUR_DOMAIN}/cancel",
        )
        
        return jsonify({"url": checkout_session.url})
        
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return jsonify({"error": str(e)}), 500




# Stripe Webhook Handler
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    print("Received event:", event["type"])

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("Checkout session completed")

        # Optional: Confirm that payment is successful (only for sync methods like card)
        # You should now rely more on the payment_intent event

    elif event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        print(f"PaymentIntent succeeded: {intent['id']}")
        
        # You can match this with your DB payment entry (if you store intent ID)
        latest_payment = Payment.query.order_by(Payment.createdAt.desc()).first()
        if latest_payment:
            latest_payment.status = "completed"
            db.session.commit()

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        print(f"PaymentIntent failed: {intent['id']}")

        # Handle failed payment
        latest_payment = Payment.query.order_by(Payment.createdAt.desc()).first()
        if latest_payment:
            latest_payment.status = "failed"
            db.session.commit()

    return "", 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0',debug=True, port=5024)




