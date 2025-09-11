# webhook.py

from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import os
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# --- Firestore Connection Setup ---
db = None
try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
    logging.info("Firestore connected using Cloud Run environment credentials.")
    db = firestore.client()
except ValueError:
    try:
        if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            cred = credentials.Certificate(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
            firebase_admin.initialize_app(cred)
            logging.info("Firestore connected using GOOGLE_APPLICATION_CREDENTIALS.")
            db = firestore.client()
        else:
            logging.warning("No GOOGLE_APPLICATION_CREDENTIALS found. Running in mock data mode.")
    except Exception as e:
        logging.error(f"Error initializing Firebase: {e}")
        logging.warning("Continuing without database connection. Using mock data.")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles a POST request from a Dialogflow CX agent."""
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
        # Extract intent (if present) and session parameters
        intent_display_name = req.get("intentInfo", {}).get("displayName")
        parameters = req.get("sessionInfo", {}).get("parameters", {})
        
        # --- FindGymIntent ---
        if intent_display_name == 'FindGymIntent':
            card_text_message = {
                "text": {
                    "text": [
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
                    ]
                }
            }
            chips_payload = {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": [
                                {
                                    "text": "Book your tour at Baltimore Wharf"
                                },
                                {
                                    "text": "Book your tour at Shoreditch"
                                },
                                {
                                    "text": "Book your tour at Moorgate"
                                }
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
            # This intent is triggered by the user selecting a gym.
            # We will now only display the dates.
            
            # Generate dates for the next 30 days
            date_options = []
            today = datetime.datetime.now()
            for i in range(30):
                date = today + datetime.timedelta(days=i)
                date_options.append({"text": date.strftime("%a %d %b")})

            combined_payload = {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": date_options
                        }
                    ]
                ]
            }
            
            fulfillment_response = {
                "fulfillmentResponse": {
                    "messages": [
                        {"text": {"text": ["Great! Please choose a day to visit us."]}},
                        {"payload": combined_payload}
                    ]
                }
            }
        
        # --- BookTourDateTimeIntent ---
        elif intent_display_name == 'BookTourDateTimeIntent':
            # This intent is triggered after the user selects a date.
            # Now we display the time slots.

            time_options = [
                {"text": "12:30"}, {"text": "13:00"}, {"text": "13:30"}, {"text": "14:00"},
                {"text": "14:30"}, {"text": "15:00"}, {"text": "15:30"}, {"text": "16:00"},
                {"text": "16:30"}, {"text": "17:00"}, {"text": "17:30"}, {"text": "18:00"},
                {"text": "18:30"}, {"text": "19:00"}, {"text": "19:30"}
            ]

            combined_payload = {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": time_options
                        }
                    ]
                ]
            }
            
            fulfillment_response = {
                "fulfillmentResponse": {
                    "messages": [
                        {"text": {"text": ["Now, please select a time:"]}},
                        {"payload": combined_payload}
                    ]
                }
            }
        
        # --- BookTourFinalIntent ---
        elif intent_display_name == 'BookTourFinalIntent':
            # This intent is triggered after the user selects both a date and time.
            date_param = parameters.get('date_param')
            time_param = parameters.get('time_param')

            if date_param and time_param:
                confirmation_message = f"Thank you! Your tour has been booked for {date_param} at {time_param}."
                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [
                            {"text": {"text": [confirmation_message]}}
                        ]
                    }
                }
            else:
                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [
                            {"text": {"text": ["Sorry, I couldn't find the date or time. Please try again."]}}
                        ]
                    }
                }   

    except Exception as e:
        logging.error(f"Webhook error: {e}")

    return jsonify(fulfillment_response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
