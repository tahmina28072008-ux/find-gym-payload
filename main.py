from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST')
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
            # This is the custom payload for a structured list of gyms.
            # In a real-world scenario, this data would be dynamically generated
            # based on user location parameters received from Dialogflow.
            gyms_payload = {
                "richContent": [
                    [
                        {
                            "type": "info",
                            "title": "Baltimore Wharf Fitness & Wellbeing Gym",
                            "subtitle": "14 Baltimore Wharf, London, E14 9FT\n020 7093 0277"
                        },
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
                        {
                            "type": "info",
                            "title": "Shoreditch Fitness & Wellbeing Gym",
                            "subtitle": "1-6 Bateman's Row, London, EC2A 3HH\n020 7739 6688"
                        },
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
                        {
                            "type": "info",
                            "title": "Moorgate Fitness & Wellbeing Gym",
                            "subtitle": "1, Ropemaker Street, London, EC2Y 9AW\n020 7920 6200"
                        },
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
            
            # Create the final fulfillment response with the custom payload
            fulfillment_response = {
                "fulfillmentResponse": {
                    "messages": [
                        {"text": {"text": ["Here are some of our nearest gyms. Which one would you like to book a tour at?"]}},
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
    app.run(debug=True, host='0.0.0.0', port=5000)
