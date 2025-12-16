
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the .env file where valid_key is stored
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"Testing Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("❌ ERROR: No API Key found in .env")
    exit(1)

genai.configure(api_key=api_key)

# We use the same model list as the prod code
models = [
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'gemini-pro',
]

print("Attempting to connect to Google Gemini...")

for model_name in models:
    try:
        print(f"Trying model: {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Hello Chef Edwin' if you are working.")
        
        print(f"\n✅ SUCCESS with {model_name}!")
        print(f"Response: {response.text}")
        break
    except Exception as e:
        print(f"❌ Failed with {model_name}: {e}")
