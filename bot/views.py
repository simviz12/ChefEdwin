from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse

@csrf_exempt
def bot_webhook(request):
    """
    Webhook to handle incoming messages from Twilio.
    """
    response = MessagingResponse()
    
    if request.method == 'POST':
        # Get the message body from the request
        msg = request.POST.get('Body', '')
        
        # Simple echo response for now
        response.message(f"You said: {msg}")
        
        return HttpResponse(str(response), content_type='text/xml')
    else:
        return HttpResponse("Method not allowed", status=405)
