import google.generativeai as genai
from django.conf import settings
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

candidates = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-002",
    "gemini-2.0-flash-exp",
    "gemini-exp-1206",
    # Fallbacks
    "gemini-pro"
]

print(f"Testing models with API Key ending in ...{api_key[-5:]}")

for model_name in candidates:
    print(f"\nTesting {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello")
        print(f"✅ SUCCESS! {model_name} is working.")
        print(f"Response: {response.text}")
        break # Found one!
    except Exception as e:
        print(f"❌ Failed: {e}")
