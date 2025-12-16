import requests
import time

def test_student_recipe():
    print(">>> Testing Student Recipe Request (Latency Check)...")
    url = 'http://127.0.0.1:8000/assistant/webhook/'
    data = {
        'Body': 'Dame una receta paso a paso para hacer spaguettis a la carbonara',
        'NumMedia': '0',
        # Using a random number that is NOT the teacher number
        'From': 'whatsapp:+57999999999'
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, data=data)
        duration = time.time() - start_time
        print(f"Status: {response.status_code}")
        print(f"Time Taken: {duration:.2f} seconds")
        print(f"Response (First 500 chars): {response.text[:500]}...")
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_student_recipe()
