from flask import Flask, request, jsonify
import logging
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import re

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Gym database with map + hours
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
        logging.error("SENDER_EMAIL or SENDER_PASSWORD environment variables are not set.")
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
    logging.info(f"Original number: {to_number}, Formatted number: {formatted_to_number}")
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
            body=body,
            to=f'whatsapp:{formatted_to_number}'
        )
        logging.info(f"WhatsApp message sent to {formatted_to_number}: {message.sid}")
    except TwilioRestException as e:
        logging.error(f"Twilio error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    fulfillment_response = {
        "fulfillmentResponse": {
            "messages": [
                {"text": {"text": ["I'm sorry, I didn't understand that. Could you please rephrase?"]}}
            ]
        }
    }

    try:
        intent_display_name = req.get("intentInfo", {}).get("displayName")
        parameters = req.get("sessionInfo", {}).get("parameters", {})

        logging.info(f"Intent: {intent_display_name}")
        logging.info(f"Parameters: {parameters}")

        # --- FindGymIntent ---
        if intent_display_name == 'FindGymIntent':
            card_text_message = {
                "text": {"text": [
                    "💪 Here are some of our nearest gyms! 🏋️‍♀️\n\n"
                    "1️⃣ **Baltimore Wharf Fitness & Wellbeing Gym**\n"
                    "📍 14 Baltimore Wharf, London, E14 9FT\n"
                    "📞 020 7093 0277\n\n"
                    "2️⃣ **Shoreditch Fitness & Wellbeing Gym**\n"
                    "📍 1-6 Bateman's Row, London, EC2A 3HH\n"
                    "📞 020 7739 6688\n\n"
                    "3️⃣ **Moorgate Fitness & Wellbeing Gym**\n"
                    "📍 1, Ropemaker Street, London, EC2Y 9AW\n"
                    "📞 020 7920 6200\n\n"
                    "👉 Which one would you like to book a tour at?"
                ]}
            }
            chips_payload = {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": [
                                {"text": "Book your tour at Baltimore Wharf", "value": "Baltimore Wharf"},
                                {"text": "Book your tour at Shoreditch", "value": "Shoreditch"},
                                {"text": "Book your tour at Moorgate", "value": "Moorgate"}
                            ]
                        }
                    ]
                ]
            }
            fulfillment_response = {
                "fulfillmentResponse": {
                    "messages": [card_text_message, {"payload": chips_payload}]
                }
            }

        # --- BookTourLocationIntent ---
        if intent_display_name == 'BookTourLocationIntent':
            gym_name = parameters.get("gymname")
            if gym_name:
                for key in GYMS.keys():
                    if key.lower() in gym_name.lower():
                        gym_name = key
                        break
            if not gym_name or gym_name not in GYMS:
                gym_name = "Baltimore Wharf"

            # Add gym info into parameters
            gym_info = GYMS[gym_name]
            parameters['gymname'] = gym_name
            parameters['gym_address'] = gym_info['address']
            parameters['gym_phone'] = gym_info['phone']
            parameters['gym_hours'] = gym_info['hours']
            parameters['gym_maps'] = gym_info['maps']
            # Generate available time slots
            combined_options = []
            start_date = datetime(2025, 9, 19)
            num_days = 5
            time_slots = [
                "12:30", "13:00", "13:30", "14:00", "14:30",
                "15:00", "15:30", "16:00", "16:30", "17:00",
                "17:30", "18:00", "18:30", "19:00", "19:30"
            ]

            for i in range(num_days):
                date = start_date + timedelta(days=i)
                for time in time_slots:
                    hour, minute = map(int, time.split(":"))
                    iso_value = datetime(
                        date.year, date.month, date.day, hour, minute
                    ).isoformat()
                    combined_options.append({
                        "text": f"{date.strftime('%a %d %b')}, {time}",
                        "value": iso_value
                    })

            combined_payload = {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": combined_options
                        }
                    ]
                ]
            }

            fulfillment_response = {
                "fulfillmentResponse": {
                    "messages": [
                        {"text": {"text": [
                            f"Great! You chose {gym_name}. Please select a date and time for your visit."
                        ]}},
                        {"payload": combined_payload}
                    ]
                }
            }

        # --- CollectUserDetailsIntent ---
        elif intent_display_name == 'CollectUserDetailsIntent' or parameters.get('first_name'):
            first_name = parameters.get('first_name')
            last_name = parameters.get('last_name')
            phone = parameters.get('phone_number')
            email = parameters.get('email')
            gymname = parameters.get('gymname', 'Baltimore Wharf')
            gym_info = GYMS[gymname]

            tour_datetime_param = parameters.get('tour_datetime')
            if tour_datetime_param and isinstance(tour_datetime_param, dict):
                try:
                    tour_date_time = datetime(
                        int(tour_datetime_param.get("year", 0)),
                        int(tour_datetime_param.get("month", 1)),
                        int(tour_datetime_param.get("day", 1)),
                        int(tour_datetime_param.get("hours", 0)),
                        int(tour_datetime_param.get("minutes", 0))
                    )
                    formatted_datetime = tour_date_time.strftime("%A, %d %B at %I:%M %p")
                except:
                    formatted_datetime = "your selected date/time"
            else:
                formatted_datetime = "your selected date/time"

            if all([first_name, last_name, phone, email]):
                # Confirmation message (chat)
                confirmation_message_plain = (
                    f"🎉 Brilliant, {first_name}! Your gym tour is now confirmed.\n\n"
                    f"🏋️‍♂️ {gymname}\n"
                    f"📍 {gym_info['address']}\n"
                    f"📞 {gym_info['phone']}\n"
                    f"🕒 Hours: {gym_info['hours']}\n"
                    f"🗓 Date & Time: {formatted_datetime}\n"
                    f"🗺 Map: {gym_info['maps']}\n\n"
                    "💡 Tip: Please arrive 10 minutes early and bring comfortable sportswear."
                )

                # Email confirmation
                confirmation_message_html = f"""
                <html>
                <body>
                    <h2>🎉 Gym Tour Confirmation</h2>
                    <p>Hi <b>{first_name}</b>, your gym tour is confirmed!</p>
                    <p>
                        🏋️‍♂️ <b>Gym:</b> {gymname}<br>
                        📍 <b>Address:</b> {gym_info['address']}<br>
                        📞 <b>Phone:</b> {gym_info['phone']}<br>
                        🕒 <b>Opening Hours:</b> {gym_info['hours']}<br>
                        🗓 <b>Date & Time:</b> {formatted_datetime}<br>
                        🗺 <b>Map:</b> <a href="{gym_info['maps']}">View on Google Maps</a>
                    </p>
                    <h3>✅ Before your visit</h3>
                    <ul>
                        <li>Arrive 10 minutes early</li>
                        <li>Wear comfortable sportswear</li>
                        <li>Bring a water bottle & towel</li>
                    </ul>
                </body>
                </html>
                """
                send_email(email, "Your Gym Tour Booking Confirmation", confirmation_message_plain, confirmation_message_html)

                # WhatsApp confirmation
                whatsapp_body = (
                    f"Hi {first_name}, your gym tour at {gymname} is confirmed 🎉\n\n"
                    f"📍 {gym_info['address']}\n"
                    f"📞 {gym_info['phone']}\n"
                    f"🕒 {gym_info['hours']}\n"
                    f"🗓 {formatted_datetime}\n"
                    f"🗺 {gym_info['maps']}\n\n"
                    "✅ Tips:\n"
                    "- Arrive 10 min early\n"
                    "- Wear sportswear\n"
                    "- Bring water & towel"
                )
                send_whatsapp_message(phone, whatsapp_body)

                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [{"text": {"text": [confirmation_message_plain]}}]
                    }
                }

    except Exception as e:
        logging.error(f"Webhook error: {e}")

    return jsonify(fulfillment_response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
