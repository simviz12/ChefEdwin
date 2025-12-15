from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
from .ai_service import get_chef_response

@csrf_exempt
def webhook(request):
    """
    Webhook to handle incoming messages from Twilio.
    Step 1.4: Receive POST requests.
    """
    if request.method == 'POST':
        # Create a TwiML response
        response = MessagingResponse()
        
        # Get the message body (optional logging or processing)
        msg = request.POST.get('Body', '')
        sender_number = request.POST.get('From', '')
        
        # Check for images (Step 3.1)
        num_media = int(request.POST.get('NumMedia', 0))
        image_url = request.POST.get('MediaUrl0') if num_media > 0 else None
        
        # Step 4.2: Simple Logic for Role Selection
        # You need to define who the teacher is. For now, we'll check an environment variable or hardcode for testing.
        import os
        teacher_number = os.getenv('TEACHER_NUMBER')
        
        role = 'student' # Default
        if teacher_number and sender_number == teacher_number:
            role = 'teacher'
            
        print(f"DEBUG: Msg from {sender_number}, Role: {role}")

        # Get response from Chef Edwin (Gemini)
        chef_reply = get_chef_response(msg, image_url=image_url, role=role)
        
        # Send the response back
        response.message(chef_reply)
        
        return HttpResponse(str(response), content_type='text/xml')
    else:
        return HttpResponse("Method not allowed", status=405)
