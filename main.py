from flask import Flask, request, jsonify
import json
import os
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

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
        # Extract intent and session parameters from the request
        intent_display_name = req.get("intentInfo", {}).get("displayName")
        parameters = req.get("sessionInfo", {}).get("parameters", {})
        
        # Check if the intent is "Find a Gym"
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

        elif intent_display_name == 'BookTourLocationIntent':
            # This intent is triggered by the user selecting a gym.
            # We now only display the dates.
            
            # Generate dates for the next 30 days
            date_options = []
            today = datetime.now()
            for i in range(30):
                date = today + timedelta(days=i)
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
                        {"text": {"text": ["Great! Please choose a day to visit us."]}, "payload": combined_payload}
                    ]
                }
            }

        elif intent_display_name == 'BookTourDateTimeIntent':
            # This new intent is triggered after the user selects a date.
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
                        {"text": {"text": ["Now, please select a time:"], "payload": combined_payload}}
                    ]
                }
            }

    
    except Exception as e:
        # Log any errors for debugging
        print(f"Webhook error: {e}")

    # Return the response as a JSON object
    return jsonify(fulfillment_response)

if __name__ == '__main__':
    # Use the PORT environment variable if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
