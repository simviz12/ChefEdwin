import requests

def test_text_message():
    print(">>> Testing Text Message...")
    url = 'http://127.0.0.1:8000/assistant/webhook/'
    data = {
        'Body': 'Hola Chef, dame una receta rápida con huevo.',
        'NumMedia': '0',
        'From': 'whatsapp:+1234567890'
    }
    try:
        response = requests.post(url, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...") # Show beginning of TwiML
    except Exception as e:
        print(f"Test Failed: {e}")

def test_image_message():
    print("\n>>> Testing Image Message (Multimodal)...")
    url = 'http://127.0.0.1:8000/assistant/webhook/'
    # Using a simple public image (example food)
    image_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/320px-Good_Food_Display_-_NCI_Visuals_Online.jpg'
    data = {
        'Body': '¿Qué puedo cocinar con esto?',
        'NumMedia': '1',
        'MediaUrl0': image_url,
        'From': 'whatsapp:+1234567890'
    }
    try:
        response = requests.post(url, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_text_message()
    test_image_message()
