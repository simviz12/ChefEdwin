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
        
        # Check for media (Step 3.1 & Audio STT)
        num_media = int(request.POST.get('NumMedia', 0))
        media_url = request.POST.get('MediaUrl0') if num_media > 0 else None
        media_type = request.POST.get('MediaContentType0', '')

        image_url = None
        audio_url = None

        if media_url:
            if media_type.startswith('image/'):
                image_url = media_url
            elif media_type.startswith('audio/'):
                audio_url = media_url

        # --- PHASE 0: AUTHENTICATION (SECURE) ---
        from .models import Student
        
        try:
            student = Student.objects.get(phone_number=sender_number)
        except Student.DoesNotExist:
            # STRICT MODE: Do not auto-create. Teacher must add them first.
            response.message("🚫 Usuario No Registrado.\nPida al profesor que lo registre en el sistema antes de continuar.")
            return HttpResponse(str(response), content_type='text/xml')
        
        if not student.is_authenticated:
            # Check hashed password
            user_input_pass = msg.strip()
            if student.check_password(user_input_pass):
                student.is_authenticated = True
                student.save()
                response.message("✅ Acceso Concedido. Bienvenido a la cocina de Chef Edwin. ¿Qué necesitas?")
                return HttpResponse(str(response), content_type='text/xml')
            else:
                response.message("🔒 Sistema Protegido.\nIntroduce tu contraseña personal para acceder.")
                return HttpResponse(str(response), content_type='text/xml')
        
        # User is authenticated, proceed
        role = student.role
        print(f"DEBUG: Msg from {sender_number}, Role: {role}, Auth: True")
        # -------------------------------

        # Get response from Chef Edwin (Gemini)
        # Step 4.3: Pass sender_number so 'The Brain' can fetch DB context
        # Updated for Audio STT
        chef_reply = get_chef_response(msg, image_url=image_url, role=role, sender_number=sender_number, audio_url=audio_url)
        
        # Send the response back
        response.message(chef_reply)
        
        # --- Step 4.3: Save History with FK Privacy (Phase 5) ---
        try:
            from .models import ConversationLog
            ConversationLog.objects.create(
                student=student,  # Foreign Key link for strict privacy
                sender_number=sender_number,
                role=role,
                message_body=msg,
                chef_response=chef_reply
            )
            print("DEBUG: Conversation saved to DB with FK link.")
        except Exception as e:
            print(f"ERROR saving to DB: {e}")
        # ----------------------------------------

        return HttpResponse(str(response), content_type='text/xml')
    else:
        return HttpResponse("Method not allowed", status=405)
