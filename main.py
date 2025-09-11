import json
import os
import requests
from flask import Flask, request, jsonify

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
        
        # Check if the intent is "Find a Gym"
        if intent_display_name == 'FindGymIntent':

            # Create the rich content payload with a list card for the gyms,
            # a single info card for one gym, and the chips.
            gyms_payload = {
                "richContent": [
                    [
                        # The list card to display all gym locations
                        {
                            "type": "list",
                            "title": "Here are some of our nearest gyms:",
                            "subtitle": "Tap on a gym for more details or to book a tour.",
                            "items": [
                                {
                                    "title": "Baltimore Wharf Fitness & Wellbeing Gym",
                                    "subtitle": "14 Baltimore Wharf, London, E14 9FT\nPhone: 020 7093 0277",
                                    "event": {
                                        "name": "book-tour",
                                        "parameters": {
                                            "gymName": "Baltimore Wharf"
                                        }
                                    }
                                },
                                {
                                    "title": "Shoreditch Fitness & Wellbeing Gym",
                                    "subtitle": "1-6 Bateman's Row, London, EC2A 3HH\nPhone: 020 7739 6688",
                                    "event": {
                                        "name": "book-tour",
                                        "parameters": {
                                            "gymName": "Shoreditch"
                                        }
                                    }
                                },
                                {
                                    "title": "Moorgate Fitness & Wellbeing Gym",
                                    "subtitle": "1, Ropemaker Street, London, EC2Y 9AW\nPhone: 020 7920 6200",
                                    "event": {
                                        "name": "book-tour",
                                        "parameters": {
                                            "gymName": "Moorgate"
                                        }
                                    }
                                }
                            ]
                        }
                    ],
                    [
                        # The info card for Baltimore Wharf
                        {
                            "type": "info",
                            "title": "Baltimore Wharf Fitness & Wellbeing Gym",
                            "subtitle": "14 Baltimore Wharf, London, E14 9FT",
                            "image": {
                                "src": {
                                    "imageUri": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Canary_Wharf_Nuffield_Health_Fitness_%26_Wellbeing_Gym_Exterior.jpg"
                                }
                            },
                            "actionLink": "https://www.nuffieldhealth.com/gyms/baltimore-wharf"
                        }
                    ],
                    [
                        # The first set of chips
                        {
                            "type": "chips",
                            "options": [
                                {
                                    "text": "Book your tour at Baltimore Wharf"
                                }
                            ]
                        }
                    ],
                    [
                        # The second set of chips
                        {
                            "type": "chips",
                            "options": [
                                {
                                    "text": "Book your tour at Shoreditch"
                                }
                            ]
                        }
                    ],
                    [
                        # The third set of chips
                        {
                            "type": "chips",
                            "options": [
                                {
                                    "text": "Book your tour at Moorgate"
                                }
                            ]
                        }
                    ]
                ]
            }
            
            # Create the final fulfillment response with the new payload
            fulfillment_response = {
                "fulfillmentResponse": {
                    "messages": [
                        {"payload": gyms_payload}
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
