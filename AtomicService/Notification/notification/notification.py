from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from os import environ
import os

app = Flask(__name__)

# Environment Variables
TWILIO_SID = environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = environ.get("TWILIO_PHONE_NUMBER")

GMAIL_USER = environ.get("GMAIL_USERNAME")
GMAIL_PASS = environ.get("GMAIL_PASSWORD")
notifications = {}
print(f"Twilio SID: {TWILIO_SID}")
print(f"Twilio Token: {TWILIO_TOKEN}")
print(f"Twilio Phone: {TWILIO_PHONE}")
print(f"Gmail User: {GMAIL_USER}")
print(f"Gmail Password: {GMAIL_PASS}")

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
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = GMAIL_USER
            msg['To'] = recipient

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(GMAIL_USER, GMAIL_PASS)
                server.send_message(msg)
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
            msg = MIMEText(notif['message'])
            msg['Subject'] = notif.get('subject', 'Reminder (Resent)')
            msg['From'] = GMAIL_USER
            msg['To'] = notif['recipient']

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(GMAIL_USER, GMAIL_PASS)
                server.send_message(msg)

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
