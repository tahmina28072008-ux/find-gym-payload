from flask import Flask, request, jsonify
import logging
import os
from datetime import datetime, timedelta

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
                "text": {"text": ["Here are some of our nearest gyms. Which one would you like to book a tour at?\n\n"
                                  "1. Baltimore Wharf Fitness & Wellbeing Gym\n"
                                  "2. Shoreditch Fitness & Wellbeing Gym\n"
                                  "3. Moorgate Fitness & Wellbeing Gym\n"]}
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
                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [
                            {"text": {"text": ["Sorry, I couldn't find the gym name. Please choose one from the options."]}}
                        ]
                    }
                }
            else:
                parameters['gym_address'] = GYMS[gym_name]['address']
                parameters['gym_phone'] = GYMS[gym_name]['phone']

                combined_options = []
                # Use today's date instead of a hardcoded date
                start_date = datetime.now()
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
            gymname = parameters.get('gymname')
            tour_datetime_param = parameters.get('tour_datetime')

            # Handle missing gymname gracefully
            if not gymname or gymname not in GYMS:
                gymname = "your selected gym"
                gym_address = "the address will be provided in a moment"
                gym_phone = "the phone number will be provided in a moment"
            else:
                gym_address = GYMS[gymname]['address']
                gym_phone = GYMS[gymname]['phone']

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

            if all([first_name, last_name, phone, email]):
                confirmation_message = (
                    f"🎉 Brilliant, {first_name}! Your gym tour is now confirmed.\n\n"
                    f"🏋️‍♂️ {gymname}\n"
                    f"📍 {gym_address}\n"
                    f"📞 {gym_phone}\n\n"
                    f"🗓 Date & Time: {formatted_datetime}\n\n"
                    f"We’ve sent a confirmation to your email at {email} and will contact you on {phone} if needed. "
                    "We can’t wait to welcome you to the gym!"
                )
                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [{"text": {"text": [confirmation_message]}}]
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

    except Exception as e:
        logging.error(f"Webhook error: {e}")

    return jsonify(fulfillment_response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
