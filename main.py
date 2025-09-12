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
            combined_options = []
            today = datetime.now()
            time_slots = ["12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30"]

            for i in range(30):
                date = today + timedelta(days=i)
                for time in time_slots:
                    combined_text = date.strftime("%a %d %b") + ", " + time
                    combined_options.append({"text": combined_text})

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
        
        
        # --- BookTourFinalIntent ---
        elif intent_display_name == 'BookTourFinalIntent':
            # Updated to handle a single datetime parameter
            tour_datetime_param = parameters.get('tour_datetime')
            
            if tour_datetime_param:
                try:
                    # Construct a datetime object from the structured data
                    tour_date_time = datetime(
                        tour_datetime_param['year'],
                        tour_datetime_param['month'],
                        tour_datetime_param['day'],
                        tour_datetime_param['hours'],
                        tour_datetime_param['minutes']
                    )
                    # Format the datetime object into a readable string
                    formatted_date_time = tour_date_time.strftime("%A, %d %B at %I:%M %p")
                    
                    # Create a simple text message for the confirmation
                    confirmation_message = f"Thank you! Your tour booking is in progress for {formatted_date_time}. To confirm the booking I need more details about you."
                    
                    # Create a rich response payload for the chips
                    continue_chips_payload = {
                        "richContent": [
                            [
                                {
                                    "type": "chips",
                                    "options": [
                                        {
                                            "text": "Continue"
                                        }
                                    ]
                                }
                            ]
                        ]
                    }

                    fulfillment_response = {
                        "fulfillmentResponse": {
                            "messages": [
                                {"text": {"text": [confirmation_message]}},
                                {"payload": continue_chips_payload}
                            ]
                        }
                    }
                except (KeyError, ValueError) as e:
                    logging.error(f"Error parsing tour_datetime: {e}")
                    fulfillment_response = {
                        "fulfillmentResponse": {
                            "messages": [
                                {"text": {"text": ["Sorry, I couldn't process the date and time. Please try again."]}
                            ]}
                    }
            else:
                fulfillment_response = {
                    "fulfillmentResponse": {
                        "messages": [
                            {"text": {"text": ["Sorry, I couldn't finalize your booking. Please try again."]}}
                        ]
                    }
                }

    except Exception as e:
        logging.error(f"Webhook error: {e}")

    return jsonify(fulfillment_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
