from flask import Flask, request, jsonify, render_template
import stripe
from flask_sqlalchemy import SQLAlchemy
import requests
from flask_cors import CORS
from os import environ

app = Flask(__name__, template_folder="templates")
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
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
# PATIENT_MICROSERVICE_URL = environ.get("PATIENT_MICROSERVICE_URL")

# Define Payment Model
class Payment(db.Model):
    __tablename__ = 'payment'
    paymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prescriptionID = db.Column(db.Integer, nullable=False)
    patientID = db.Column(db.Integer, nullable=False)
    patientEmail = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float(precision=2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    stripeSessionID = db.Column(db.String(255), nullable=True)
    createdAt = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updatedAt = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def json(self):
        return {
            "paymentID": self.paymentID,
            "prescriptionID": self.prescriptionID,
            "amount": self.amount,
            "status": self.status,
            "createdAt": self.createdAt,
            "checkout_url": None
        }

@app.route("/")
def home():
    return render_template("index.html", stripe_publishable_key=STRIPE_PUBLISHABLE_KEY)

@app.route("/successrecreatedsession")
def successrecreatedsession():
    return render_template("successrecreatedsession.html")

@app.route("/successfirstsession")
def successfirstsession():
    return render_template("successfirstsession.html")

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

@app.route("/error")
def error():
    return render_template("error.html")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No data provided"}), 400

        patient_id = request_data.get('patient_id')
        patient_email = request_data.get('patient_email')
        prescription_id = request_data.get('prescription_id')
        medicines = request_data.get('medicines', [])

        if not patient_id or not patient_email or not prescription_id or not medicines:
            return jsonify({"error": "Missing required fields."}), 400

        consultation_fee = 2000
        total_price = sum(m.get("price", 0) for m in medicines) + consultation_fee

        new_payment = Payment(
            prescriptionID=prescription_id,
            patientID=patient_id,
            patientEmail=patient_email,
            amount=total_price * 100,
            status="pending"
        )
        db.session.add(new_payment)
        db.session.commit()

        session = stripe.checkout.Session.create(
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
            success_url=f"{YOUR_DOMAIN}/successfirstsession",
            cancel_url=f"{YOUR_DOMAIN}/cancel",
            metadata={"payment_id": str(new_payment.paymentID)}
        )

        new_payment.stripeSessionID = session.id
        db.session.commit()

        return jsonify({"url": session.url})

    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        print("⚠️ Invalid payload:", str(e))
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        print("⚠️ Invalid signature:", str(e))
        return "Invalid signature", 400

    print("✅ Webhook received event:", event["type"])
    print("🔍 Event data:", event["data"])

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        payment_id = metadata.get("payment_id")
        print("👉 checkout.session.completed - payment_id from metadata:", payment_id)

        # Fallback to PaymentIntent metadata
        if not payment_id and "payment_intent" in session:
            try:
                intent = stripe.PaymentIntent.retrieve(session["payment_intent"])
                metadata = intent.get("metadata", {})
                payment_id = metadata.get("payment_id")
                print("👉 Fallback - payment_id from PaymentIntent metadata:", payment_id)
            except Exception as e:
                print("❌ Error retrieving intent metadata:", str(e))

        if payment_id:
            payment = Payment.query.filter_by(paymentID=int(payment_id)).first()
            if payment:
                print(f"✅ Updating payment ID {payment_id} to completed")
                payment.status = "completed"
                db.session.commit()
            else:
                print(f"❌ No payment record found for ID {payment_id}")

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        metadata = intent.get("metadata", {})
        payment_id = metadata.get("payment_id")
        print("👉 payment_intent.payment_failed - payment_id:", payment_id)

        if payment_id:
            payment = Payment.query.filter_by(paymentID=int(payment_id)).first()
            if payment:
                print(f"❌ Updating payment ID {payment_id} to failed")
                payment.status = "failed"
                db.session.commit()
            else:
                print(f"❌ No payment record found for ID {payment_id}")

    return "", 200


@app.route("/patient/<int:patient_id>/pending-payments", methods=["GET"])
def get_pending_payments(patient_id):
    try:
        pending = Payment.query.filter_by(patientID=patient_id, status='pending').order_by(Payment.createdAt.desc()).all()
        return jsonify({"code": 200, "data": [p.json() for p in pending]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/payment/<int:payment_id>/recreate-session", methods=["POST"])
def recreate_checkout_session(payment_id):
    payment = Payment.query.get(payment_id)

    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    if payment.status != "pending":
        return jsonify({"error": "Only pending payments can be regenerated"}), 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card", "paynow"],
            line_items=[{
                "price_data": {
                    "currency": "sgd",
                    "product_data": {"name": "Doctor Consultation & Medicines"},
                    "unit_amount": int(payment.amount * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=payment.patientEmail,
            success_url=f"{YOUR_DOMAIN}/successrecreatedsession",
            cancel_url=f"{YOUR_DOMAIN}/cancel",
            metadata={"payment_id": str(payment.paymentID)}
        )

        payment.stripeSessionID = session.id
        db.session.commit()

        return jsonify({"url": session.url}), 200

    except Exception as e:
        print(f"Error creating Stripe session: {e}")
        return jsonify({"error": "Failed to create Stripe session"}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5024)











