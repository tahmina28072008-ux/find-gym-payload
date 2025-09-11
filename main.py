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
            # Create a text message with gym details
            gyms_text_message = {
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

            # Create the rich content payload with only the chips
            gyms_payload = {
                "richContent": [
                    [
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
            
            # Create the final fulfillment response with both text and payload messages
            fulfillment_response = {
                "fulfillmentResponse": {
                    "messages": [
                        gyms_text_message,
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
