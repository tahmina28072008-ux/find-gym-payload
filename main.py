from flask import Flask, request, jsonify
import logging
import os
import datetime

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
            date_options = []
            today = datetime.datetime.now()
            for i in range(30):
                date = today + datetime.timedelta(days=i)
                date_options.append({"text": date.strftime("%a %d %b")})

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
                            "options": date_options
                        }
                    ],
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
                        {"text": {"text": ["Great! Please choose a date and time for your visit."]}},
                        {"payload": combined_payload}
                    ]
                }
            }
        
        # --- BookTourDateTimeIntent - This intent is now obsolete as the logic is merged with BookTourLocationIntent.
        elif intent_display_name == 'BookTourDateTimeIntent':
            fulfillment_response = {
                "fulfillmentResponse": {
                    "messages": [
                        {"text": {"text": ["This intent is no longer active. Please select a date and time from the options provided previously."]}}
                    ]
                }
            }
        
        # --- BookTourFinalIntent ---
        elif intent_display_name == 'BookTourFinalIntent':
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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
