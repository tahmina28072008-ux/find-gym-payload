from flask import Flask, request, jsonify
import logging
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles a POST request for the Locations Flow from a Dialogflow CX agent."""
    req = request.get_json(silent=True, force=True)

    # Default fallback response
    fulfillment_response = {
        "fulfillmentResponse": {
            "messages": [
                {"text": {"text": ["I'm sorry, I didn't understand that. Could you please rephrase?"]}}
            ]
        }
    }

    try:
        # Extract intent and session parameters
        intent_display_name = req.get("intentInfo", {}).get("displayName")
        parameters = req.get("sessionInfo", {}).get("parameters", {})

        logging.info(f"Intent: {intent_display_name}")
        logging.info(f"Parameters: {parameters}")

        # --- FindGymIntent ---
        if intent_display_name == 'FindGymIntent':
            card_text_message = {
                "text": {
                    "text": [
                        "Here are some of our nearest gyms. Which one would you like to book a tour at?\n\n"
                        "1. Baltimore Wharf Fitness & Wellbeing Gym\n"
                        "2. Shoreditch Fitness & Wellbeing Gym\n"
                        "3. Moorgate Fitness & Wellbeing Gym\n"
                    ]
                }
            }
            chips_payload = {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": [
                                {"text": "Book your tour at Baltimore Wharf"},
                                {"text": "Book your tour at Shoreditch"},
                                {"text": "Book your tour at Moorgate"}
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
            combined_options = []

            # Start date: 13th September 2025
            start_date = datetime(2025, 9, 13)
            num_days = 7  # next 7 days
            time_slots = ["12:30", "13:00", "13:30", "14:00", "14:30",
                          "15:00", "15:30", "16:00", "16:30", "17:00",
                          "17:30", "18:00", "18:30", "19:00", "19:30"]

            for i in range(num_days):
                date = start_date + timedelta(days=i)
                for time in time_slots:
                    combined_text = date.strftime("%a %d %b") + ", " + time
                    hour, minute = map(int, time.split(":"))
                    iso_value = datetime(date.year, date.month, date.day, hour, minute).isoformat()
                    combined_options.append({
                        "text": combined_text,
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
                        {"text": {"text": ["Great! Please choose a date and time for your visit."]}},
                        {"payload": combined_payload}
                    ]
                }
            }

        # --- Handle date/time selection ---
        elif parameters.get('tour_datetime'):
            tour_datetime_param = parameters.get('tour_datetime')
            logging.info(f"Raw tour_datetime param: {tour_datetime_param}")
            tour_date_time = None

            try:
                if isinstance(tour_datetime_param, str):
                    # plain ISO string
                    tour_date_time = datetime.fromisoformat(
                        tour_datetime_param.replace("Z", "+00:00")
                    )

                elif isinstance(tour_datetime_param, dict):
                    # dictionary with startDateTime
                    if "startDateTime" in tour_datetime_param:
                        tour_date_time = datetime.fromisoformat(
                            tour_datetime_param["startDateTime"].replace("Z", "+00:00")
                        )

                elif isinstance(tour_datetime_param, list) and len(tour_datetime_param) > 0:
                    first_item = tour_datetime_param[0]
                    if isinstance(first_item, dict) and "startDateTime" in first_item:
                        tour_date_time = datetime.fromisoformat(
                            first_item["startDateTime"].replace("Z", "+00:00")
                        )

                if tour_date_time:
                    formatted_date_time = tour_date_time.strftime("%A, %d %B at %I:%M %p")
                    confirmation_message = (
                        f"Thank you! Your tour booking is in progress for {formatted_date_time}. "
                        "To confirm the booking I need more details about you."
                    )

                    fulfillment_response = {
                        "fulfillmentResponse": {
                            "messages": [
                                {"text": {"text": [confirmation_message]}}
                            ]
                        }
                    }
                else:
                    raise ValueError("Unsupported format for tour_datetime")

            except Exception as e:
                logging.error(f"Error parsing tour_datetime: {e}")
                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [
                            {"text": {"text": [
                                "Sorry, I couldn't process the date and time. Please try again."
                            ]}}
                        ]
                    }
                }

    except Exception as e:
        logging.error(f"Webhook error: {e}")

    return jsonify(fulfillment_response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
