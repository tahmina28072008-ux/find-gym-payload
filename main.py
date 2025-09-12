from flask import Flask, request, jsonify
import logging
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Gym database
GYMS = {
    "Baltimore Wharf": {
        "address": "14 Baltimore Wharf, London, E14 9FT",
        "phone": "020 7093 0277"
    },
    "Shoreditch": {
        "address": "1-6 Bateman's Row, London, EC2A 3HH",
        "phone": "020 7739 6688"
    },
    "Moorgate": {
        "address": "1, Ropemaker Street, London, EC2Y 9AW",
        "phone": "020 7920 6200"
    }
}

# --- Email Helper ---
def send_email(to_email, subject, plain_body, html_body):
    """Sends an email with both plain text and HTML versions."""
    sender_email = "niljoshna28@gmail.com"  # Replace with your email
    sender_password = "nxlcscihekyxcedc"  # Gmail App Password

    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach both parts of the message.
    part1 = MIMEText(plain_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logging.info(f"Email sent to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

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
                        "Here are some of our nearest gyms. Which one would you like to book a tour at?\n\n"
                        "1. Baltimore Wharf Fitness & Wellbeing Gym\n"
                        "   14 Baltimore Wharf, London, E14 9FT\n"
                        "   Phone: 020 7093 0277\n\n"
                        "2. Shoreditch Fitness & Wellbeing Gym\n"
                        "   1-6 Bateman's Row, London, EC2A 3HH\n"
                        "   Phone: 020 7739 6688\n\n"
                        "3. Moorgate Fitness & Wellbeing Gym\n"
                        "   1, Ropemaker Street, London, EC2Y 9AW\n"
                        "   Phone: 020 7920 6200\n"
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
        elif intent_display_name == 'BookTourLocationIntent':
            gym_name = parameters.get("gymname")
            if not gym_name or gym_name not in GYMS:
                gym_name = "Baltimore Wharf"

            # Automatically store gym details in session parameters
            parameters['gymname'] = gym_name
            parameters['gym_address'] = GYMS[gym_name]['address']
            parameters['gym_phone'] = GYMS[gym_name]['phone']

            combined_options = []
            start_date = datetime(2025, 9, 13)
            num_days = 7
            time_slots = ["12:30", "13:00", "13:30", "14:00", "14:30",
                          "15:00", "15:30", "16:00", "16:30", "17:00",
                          "17:30", "18:00", "18:30", "19:00", "19:30"]

            for i in range(num_days):
                date = start_date + timedelta(days=i)
                for time in time_slots:
                    hour, minute = map(int, time.split(":"))
                    iso_value = datetime(date.year, date.month, date.day, hour, minute).isoformat()
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
                        {"text": {"text": [f"Great! You chose {gym_name}. Please select a date and time for your visit."]}},
                        {"payload": combined_payload}
                    ]
                }
            }

        # --- CollectUserDetailsIntent ---
        elif intent_display_name == 'CollectUserDetailsIntent' or parameters.get('first_name'):
            first_name_param = parameters.get('first_name')
            last_name_param = parameters.get('last_name')
            phone = parameters.get('phone_number')
            email = parameters.get('email')
            gymname = parameters.get('gymname', 'Baltimore Wharf')
            gym_address = parameters.get('gym_address', GYMS[gymname]['address'])
            gym_phone = parameters.get('gym_phone', GYMS[gymname]['phone'])
            tour_datetime_param = parameters.get('tour_datetime')
            
            first_name = first_name_param.get("name") if isinstance(first_name_param, dict) else first_name_param
            last_name = last_name_param.get("name") if isinstance(last_name_param, dict) else last_name_param

            if tour_datetime_param:
                if isinstance(tour_datetime_param, dict):
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
                    formatted_datetime = str(tour_datetime_param)
            else:
                formatted_datetime = "your selected date/time"

            # Check if all details are provided
            if all([first_name, last_name, phone, email]):
                confirmation_message_plain = (
                    f"🎉 Brilliant, {first_name}! Your gym tour is now confirmed.\n\n"
                    f"🏋️‍♂️ {gymname}\n"
                    f"📍 {gym_address}\n"
                    f"📞 {gym_phone}\n\n"
                    f"🗓 Date & Time: {formatted_datetime}\n\n"
                    f"We’ve sent a confirmation to your email at {email} and will contact you on {phone} if needed. "
                    "We can’t wait to welcome you to the gym!"
                )

                confirmation_message_html = f"""
                <html>
                <body>
                    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <h1 style="color: #007BFF; text-align: center;">Gym Tour Confirmation</h1>
                        <p>🎉 Brilliant, <strong>{first_name}</strong>! Your gym tour is now confirmed.</p>
                        
                        <p style="background-color: #f4f4f4; padding: 15px; border-radius: 8px;">
                            <strong>🏋️‍♂️ Gym:</strong> {gymname}<br>
                            <strong>📍 Address:</strong> {gym_address}<br>
                            <strong>📞 Phone:</strong> {gym_phone}
                        </p>
                        
                        <p><strong>🗓 Date & Time:</strong> {formatted_datetime}</p>
                                          
                        <p>We can’t wait to welcome you to the gym!</p>
                        
                        <hr style="border: 0; height: 1px; background: #ddd; margin: 20px 0;">
                        <p style="font-size: 12px; color: #888; text-align: center;">This is an automated email. Please do not reply.</p>
                    </div>
                </body>
                </html>
                """

                # --- Send Email ---
                email_subject = "Your Gym Tour Booking Confirmation"
                send_email(email, email_subject, confirmation_message_plain, confirmation_message_html)

                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [{"text": {"text": [confirmation_message_plain]}}]
                    }
                }
            else:
                missing_fields = []
                if not first_name: missing_fields.append("first name")
                if not last_name: missing_fields.append("last name")
                if not phone: missing_fields.append("mobile number")
                if not email: missing_fields.append("email address")
                prompt_message = (
                    f"Almost there! Please provide your {' and '.join(missing_fields)} so we can confirm your booking."
                )
                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [{"text": {"text": [prompt_message]}}]
                    }
                }

        # --- Handle tour_datetime before CollectUserDetails ---
        elif parameters.get('tour_datetime'):
            tour_datetime_param = parameters.get('tour_datetime')
            logging.info(f"Raw tour_datetime param: {tour_datetime_param}")
            tour_date_time = None
            try:
                if isinstance(tour_datetime_param, dict):
                    tour_date_time = datetime(
                        int(tour_datetime_param.get("year", 0)),
                        int(tour_datetime_param.get("month", 1)),
                        int(tour_datetime_param.get("day", 1)),
                        int(tour_datetime_param.get("hours", 0)),
                        int(tour_datetime_param.get("minutes", 0))
                    )
                if tour_date_time:
                    formatted_date_time = tour_date_time.strftime("%A, %d %B at %I:%M %p")
                    confirmation_message = (
                        f"Thank you! Your tour booking is in progress for {formatted_date_time}. "
                        "To confirm the booking I need more details about you."
                    )
                    fulfillment_response = {
                        "fulfillmentResponse": {
                            "messages": [{"text": {"text": [confirmation_message]}}]
                        }
                    }
            except Exception as e:
                logging.error(f"Error parsing tour_datetime: {e}")
                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [
                            {"text": {"text": ["Sorry, I couldn't process the date and time. Please try again."]}}
                        ]
                    }
                }

    except Exception as e:
        logging.error(f"Webhook error: {e}")

    return jsonify(fulfillment_response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
