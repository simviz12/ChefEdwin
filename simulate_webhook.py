
import requests
import os
from dotenv import load_dotenv

# Load env to get credentials if needed (though we just simulate POST)
load_dotenv()

# URL of the deployed webhook
# WEBHOOK_URL = 'http://localhost:8000/assistant/webhook/' # Local testing
WEBHOOK_URL = 'https://chefedwin.onrender.com/assistant/webhook/' # Production

def simulate_whatsapp_message(body_text, from_number='whatsapp:+573001234567'):
    print(f"--- Simulating Message: '{body_text}' ---")
    print(f"Sending to: {WEBHOOK_URL}")
    
    payload = {
        'AccountSid': 'AC_SIMULATED_ACCOUNT',
        'From': from_number,
        'Body': body_text,
        'NumMedia': '0'
    }
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload)
        
        print(f"Status Code: {response.status_code}")
        print("Response Content (TwiML):")
        print(response.text)
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Webhook received and processed message!")
        else:
            print(f"\n❌ ERROR: Server returned {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    # Simulate a user saying "Hola"
    simulate_whatsapp_message("Hola Chef Edwin")
    
    # Simulate a student question
    simulate_whatsapp_message("¿Cuáles son los ingredientes del merengue francés?")
