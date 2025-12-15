import google.generativeai as genai
from django.conf import settings
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")

genai.configure(api_key=api_key)

try:
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
