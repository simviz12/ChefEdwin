
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print("Searching for a working model...")
working_model = None

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Testing {m.name}...")
            try:
                model = genai.GenerativeModel(m.name)
                res = model.generate_content("Hello")
                if res and res.text:
                    print(f"✅ SUCCESS: {m.name}")
                    working_model = m.name
                    break
            except Exception as e:
                print(f"❌ Failed: {e}")
except Exception as e:
    print(f"Critical Error: {e}")

if working_model:
    print(f"FOUND WORKING MODEL: {working_model}")
else:
    print("NO WORKING MODEL FOUND")
