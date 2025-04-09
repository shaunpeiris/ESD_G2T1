from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import os
from mailersend import emails
import traceback

app = Flask(__name__)

# Load environment variables
load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

notifications = {}

@app.route('/notify', methods=['POST'])
def send_notification():
    data = request.json
    notif_id = str(len(notifications) + 1)
    message = data.get('message')
    recipient = data.get('recipient')
    method = data.get('method')  # "sms" or "email"
    subject = data.get('subject', 'Appointment Reminder')

    try:
        if method == 'sms':
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            client.messages.create(
                body=message,
                from_=TWILIO_PHONE,
                to=recipient
            )
        elif method == 'email':
            mailer = emails.NewEmail(MAILERSEND_API_KEY)
            mail_body = {}

            mail_from = {"email": SENDER_EMAIL}
            recipients = [{"email": recipient}]

            mailer.set_mail_from(mail_from, mail_body)
            mailer.set_mail_to(recipients, mail_body)
            mailer.set_subject(subject, mail_body)
            mailer.set_plaintext_content(message, mail_body)

            mailer.send(mail_body)
        else:
            return jsonify({'error': 'Invalid method'}), 400

        notifications[notif_id] = {
            'recipient': recipient,
            'message': message,
            'subject': subject,
            'method': method,
            'status': 'sent'
        }

        return jsonify({'notification_id': notif_id, 'status': 'sent'}), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/notify/resend/<notif_id>', methods=['POST'])
def resend_notification(notif_id):
    notif = notifications.get(notif_id)
    if not notif:
        return jsonify({'error': 'Notification not found'}), 404

    try:
        if notif['method'] == 'sms':
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            client.messages.create(
                body=notif['message'],
                from_=TWILIO_PHONE,
                to=notif['recipient']
            )
        elif notif['method'] == 'email':
            mailer = emails.NewEmail(MAILERSEND_API_KEY)
            mail_body = {}

            mail_from = {"email": SENDER_EMAIL}
            recipients = [{"email": notif['recipient']}]

            mailer.set_mail_from(mail_from, mail_body)
            mailer.set_mail_to(recipients, mail_body)
            mailer.set_subject(notif.get('subject', 'Reminder (Resent)'), mail_body)
            mailer.set_plaintext_content(notif['message'], mail_body)

            mailer.send(mail_body)

        notif['status'] = 'resent'
        return jsonify({'notification_id': notif_id, 'status': 'resent'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5005)



######Use this to trigger notifications in your microservice######

# import requests

# NOTIF_SERVICE_URL = "http://localhost:5200"

# def send_sms(to_phone, message):
#     payload = {
#         "method": "sms",
#         "recipient": to_phone,
#         "message": message
#     }
#     response = requests.post(f"{NOTIF_SERVICE_URL}/notify", json=payload)
#     return response.json()


# def send_email(to_email, subject, message):
#     payload = {
#         "method": "email",
#         "recipient": to_email,
#         "subject": subject,
#         "message": message
#     }
#     response = requests.post(f"{NOTIF_SERVICE_URL}/notify", json=payload)
#     return response.json()


# def resend_notification(notification_id):
#     response = requests.post(f"{NOTIF_SERVICE_URL}/notify/resend/{notification_id}")
#     return response.json()
