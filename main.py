from flask import Flask, request, jsonify
import logging
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import re

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Gym database with opening hours
GYMS = {
    "Baltimore Wharf": {
        "address": "14 Baltimore Wharf, London, E14 9FT",
        "phone": "020 7093 0277",
        "maps": "https://www.google.com/maps?q=14+Baltimore+Wharf,+London,+E14+9FT",
        "hours": "Mon–Fri: 6:00 AM – 10:00 PM, Sat–Sun: 8:00 AM – 8:00 PM"
    },
    "Shoreditch": {
        "address": "1-6 Bateman's Row, London, EC2A 3HH",
        "phone": "020 7739 6688",
        "maps": "https://www.google.com/maps?q=1-6+Bateman's+Row,+London,+EC2A+3HH",
        "hours": "Mon–Fri: 6:30 AM – 9:30 PM, Sat–Sun: 9:00 AM – 7:00 PM"
    },
    "Moorgate": {
        "address": "1, Ropemaker Street, London, EC2Y 9AW",
        "phone": "020 7920 6200",
        "maps": "https://www.google.com/maps?q=1+Ropemaker+Street,+London,+EC2Y+9AW",
        "hours": "Mon–Fri: 6:00 AM – 9:00 PM, Closed on Weekends"
    }
}

# --- Email Helper ---
def send_email(to_email, subject, plain_body, html_body):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        logging.error("SENDER_EMAIL or SENDER_PASSWORD not set.")
        return

    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(plain_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logging.info(f"Email sent to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# --- Twilio Helper ---
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def format_phone_number(phone_number):
    clean_number = re.sub(r'[\s\-()]+', '', phone_number)
    if clean_number.startswith('+'):
        return clean_number
    if clean_number.startswith('0'):
        return f'+44{clean_number[1:]}'
    return f'+{clean_number}'

def send_whatsapp_message(to_number, body):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logging.error("Twilio credentials missing.")
        return
    if not TWILIO_PHONE_NUMBER:
        logging.error("TWILIO_PHONE_NUMBER not set.")
        return

    formatted_to_number = format_phone_number(to_number)
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
            body=body,
            to=f'whatsapp:{formatted_to_number}'
        )
        logging.info(f"WhatsApp sent: {message.sid}")
    except TwilioRestException as e:
        logging.error(f"Twilio error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    fulfillment_response = {
        "fulfillmentResponse": {
            "messages": [{"text": {"text": ["Sorry, I didn’t catch that. Can you try again?"]}}]
        }
    }

    try:
        intent_display_name = req.get("intentInfo", {}).get("displayName")
        params = req.get("sessionInfo", {}).get("parameters", {})

        logging.info(f"Intent: {intent_display_name}, Params: {params}")

        if intent_display_name == 'CollectUserDetailsIntent' or params.get('first_name'):
            first_name = params.get('first_name')
            last_name = params.get('last_name')
            phone = params.get('phone_number')
            email = params.get('email')
            gymname = params.get('gymname', 'Baltimore Wharf')
            gym_info = GYMS[gymname]

            # Format date & time
            formatted_datetime = "your selected date/time"
            tour_datetime = params.get('tour_datetime')
            if isinstance(tour_datetime, dict):
                try:
                    dt = datetime(
                        int(tour_datetime.get("year", 0)),
                        int(tour_datetime.get("month", 1)),
                        int(tour_datetime.get("day", 1)),
                        int(tour_datetime.get("hours", 0)),
                        int(tour_datetime.get("minutes", 0))
                    )
                    formatted_datetime = dt.strftime("%A, %d %B at %I:%M %p")
                except:
                    pass

            if all([first_name, last_name, phone, email]):
                # --- Chat confirmation ---
                chat_message = (
                    f"🎉 Great, {first_name}! Your gym tour is confirmed.\n\n"
                    f"🏋️‍♂️ {gymname}\n"
                    f"📍 {gym_info['address']}\n"
                    f"📞 {gym_info['phone']}\n"
                    f"🗓 {formatted_datetime}\n"
                    f"⏰ Opening Hours: {gym_info['hours']}\n\n"
                    f"🗺 Map: {gym_info['maps']}\n\n"
                    "💡 Tip: Please arrive 10 minutes early and bring comfortable sportswear."
                )

                # --- Email confirmation ---
                email_html = f"""
                <html>
                <body>
                    <div style="font-family: Arial, sans-serif; max-width:600px; margin:auto;">
                        <h2 style="color:#007BFF;">Gym Tour Confirmation</h2>
                        <p>🎉 Great, <b>{first_name}</b>! Your gym tour has been confirmed.</p>
                        <p>
                            <b>🏋️‍♂️ Gym:</b> {gymname}<br>
                            <b>📍 Address:</b> {gym_info['address']}<br>
                            <b>📞 Phone:</b> {gym_info['phone']}<br>
                            <b>🗓 Date & Time:</b> {formatted_datetime}<br>
                            <b>⏰ Opening Hours:</b> {gym_info['hours']}<br>
                            <b>🗺 Map:</b> <a href="{gym_info['maps']}">View on Google Maps</a>
                        </p>
                        <h3>✅ Before your visit</h3>
                        <ul>
                            <li>Arrive at least 10 minutes early.</li>
                            <li>Wear comfortable sportswear and trainers.</li>
                            <li>Bring a water bottle and towel.</li>
                        </ul>
                        <p>Looking forward to welcoming you!</p>
                    </div>
                </body>
                </html>
                """
                send_email(email, "Your Gym Tour Confirmation", chat_message, email_html)

                # --- WhatsApp confirmation ---
                whatsapp_body = (
                    f"Hi {first_name}, your gym tour at {gymname} is confirmed! 🎉\n\n"
                    f"📍 {gym_info['address']}\n"
                    f"📞 {gym_info['phone']}\n"
                    f"🗓 {formatted_datetime}\n"
                    f"⏰ Opening Hours: {gym_info['hours']}\n"
                    f"🗺 Map: {gym_info['maps']}\n\n"
                    "✅ Please:\n- Arrive 10 minutes early\n- Wear sportswear\n- Bring water & a towel\n\n"
                    "Looking forward to welcoming you!"
                )
                send_whatsapp_message(phone, whatsapp_body)

                fulfillment_response = {
                    "fulfillmentResponse": {"messages": [{"text": {"text": [chat_message]}}]}
                }

    except Exception as e:
        logging.error(f"Webhook error: {e}")

    return jsonify(fulfillment_response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
