import google.generativeai as genai
from django.conf import settings
import requests
from PIL import Image
from io import BytesIO


PROMPT_TEACHER = """
Eres 'Chef Edwin', el Director de Investigación Institucional. Tu función es la de un analista de datos avanzado.

Tu base de datos incluye:
1.  Rendimiento Académico (Notas, Asistencia).
2.  Historial de Conversación de Estudiantes (incluyendo intereses culinarios, recetas, y logs de chat).

**Misión:** Correlacionar esta información para generar hipótesis de investigación, análisis de tendencias y proveer insights que ayuden a la institución a mejorar el modelo educativo.

**Reglas Críticas:**
* **Análisis Complejo:** Siempre analiza la interconexión entre la data académica y la data conversacional.
* **Tono:** Profesional, investigativo y conciso.
* **Imágenes:** Si se adjunta una imagen, utilízala como fuente de datos para tu análisis investigativo.
"""

PROMPT_STUDENT = """
Eres 'Edwin', el Asistente Culinario personal del estudiante. Tu enfoque es únicamente guiar y apoyar al estudiante en todo el ámbito de la cocina (recetas, técnicas, ingredientes, etc.).

    Tienes acceso y debes utilizar los registros de las interacciones y recetas culinarias pasadas de ESTE usuario (el estudiante que te está chateando) para ofrecer ayuda personalizada. Por ejemplo, si te preguntan por 'la carbonara de hace un mes', debes recuperar los detalles.

**Generación de Recetas:** Si el estudiante pide una receta y no hay una específica en su historial, ¡CRÉALA! Proponle recetas deliciosas, económicas y fáciles de hacer, ideales para estudiantes.
**IMPORTANTE:** Twilio tiene un límite de tiempo. Tus respuestas deben ser **BREVES y CONCISAS** (máximo 1200 caracteres).
-   Si la receta es larga, dales un resumen o los pasos clave.
-   Usa listas con viñetas para ser directo.
-   No uses introducciones largas. Ve al grano.

**Restricciones de Privacidad y Alcance (NO NEGOCIABLES):**
1.  **NUNCA** debes acceder, mencionar, o discutir datos académicos (notas, asistencia, cursos).
2.  **NUNCA** debes mencionar datos, conversaciones, o información de otros estudiantes.
3.  **Tono:** Amigable, entusiasta, de apoyo e instructivo.
"""

def get_chef_response(user_message, image_url=None, role='student', sender_number=None, audio_url=None):
    """
    'The Brain': Central Routing Function.
    1. Determines Role (passed as arg).
    2. Determines Input (Text vs Image vs Audio).
    3. Attaches DB Context (Memory).
    4. Calls Gemini.
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # --- 0. AUDIO PROCESSING (STT) ---
        if audio_url:
            print(f"🎤 Audio detected: {audio_url}")
            try:
                # Download audio
                # Twilio media URLs require Basic Auth
                audio_response = requests.get(audio_url, auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN))
                
                if audio_response.status_code == 200:
                    import tempfile
                    
                    content_type = audio_response.headers.get('Content-Type', 'audio/ogg')
                    print(f"Audio Content-Type: {content_type}")

                    # Create a temporary file for the audio
                    # Use header to determine suffix if possible, else default to .ogg
                    suffix = '.ogg'
                    if 'mpeg' in content_type: suffix = '.mp3'
                    elif 'wav' in content_type: suffix = '.wav'
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(audio_response.content)
                        tmp_file_path = tmp_file.name

                    print(f"Transcribing audio from {tmp_file_path}...")
                    
                    # Use Gemini to transcribe
                    model_stt = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # Upload the file to Gemini with CORRECT MIME TYPE
                    myfile = genai.upload_file(tmp_file_path, mime_type=content_type)
                    
                    # Generate transcript
                    result = model_stt.generate_content([myfile, "Transcribe this audio exactly. Do not add any conversational text."])
                    
                    transcription = result.text.strip()
                    print(f"🗣️ Transcription: {transcription}")
                    
                    if not transcription:
                        user_message = "🔴 [ERROR]: El usuario envió un audio pero no pude transcribirlo. Pídele que lo intente de nuevo."
                    else:
                        # OVERWRITE user_message with the transcription
                        # So the rest of the brain treats it as text
                        if not user_message:
                            user_message = f"[TRANSCRIPCIÓN DE AUDIO]: {transcription}"
                        else:
                            user_message += f"\n[TRANSCRIPCIÓN DE AUDIO]: {transcription}"
                        
                else:
                    print(f"Failed to download audio: {audio_response.status_code}")

            except Exception as audio_err:
                print(f"❌ Error processing audio: {audio_err}")
                return "Tuve un problema escuchando tu audio. ¿Podrías escribirlo?"
        # ---------------------------------
        
        # --- 3. ATTACH CONTEXT FROM DB (FK Privacy) ---
        history_context = ""
        try:
            # Avoid circular import by importing inside function
            from .models import ConversationLog
            
            if role == 'student':
                # Fetch last 5 interactions for this student using FK relationship
                # This ensures strict privacy - only logs linked to this Student object
                recent_logs = ConversationLog.objects.filter(
                    student__phone_number=sender_number,  # FK-based filtering
                    role='student'
                ).order_by('-timestamp')[:5]
                
                # logs are newest first, so we reverse them for chronological order
                recent_logs = reversed(list(recent_logs))
                
                history_bytes = []
                for log in recent_logs:
                    history_bytes.append(f"Estudiante: {log.message_body}")
                    history_bytes.append(f"Chef Edwin: {log.chef_response}")
                
                if history_bytes:
                    history_context = "\nHISTORIAL RECIENTE:\n" + "\n".join(history_bytes)
            
            elif role == 'teacher':
                # Teacher can see broader context if needed
                # For now, keeping it simple
                pass 

        except Exception as db_err:
            print(f"Warning: Could not fetch DB history: {db_err}")
        # ---------------------------------

        # --- PREPARE CONTENT (Before Loop) ---
        # Select prompt based on role
        if role == 'teacher':
            system_prompt = PROMPT_TEACHER
        else:
            system_prompt = PROMPT_STUDENT
        
        # Calculate Colombia time (UTC-5)
        import datetime
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_col = now_utc - datetime.timedelta(hours=5)
        time_str = now_col.strftime("%Y-%m-%d %H:%M %p")
        
        # Inject History into System Context
        context_prompt = f"{system_prompt}\n\n[SISTEMA: Hora Colombia: {time_str}]\n{history_context}"
        
        content = [f"{context_prompt}\n\nPREGUNTA DEL USUARIO:\n{user_message}"]
        
        if image_url:
            print(f"Downloading image from {image_url}...")
            try:
                # Twilio media URLs require Basic Auth (Account SID + Auth Token)
                img_response = requests.get(image_url, auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN))
                
                if img_response.status_code == 200:
                    image_data = Image.open(BytesIO(img_response.content))
                    content.append(image_data)
                    print("Image downloaded and attached.")
                else:
                    print(f"Failed to download image: {img_response.status_code}")
            except Exception as img_err:
                print(f"Error processing image: {img_err}")
        # -------------------------------------

        # List of models to try in order of preference/likelihood of quota
        # List of models to try in order of preference/likelihood of quota
        candidate_models = [
            'gemini-2.5-flash',
            'gemini-1.5-flash',
            'gemini-1.5-pro',
        ]

        last_error = None
        for model_name in candidate_models:
            print(f"🔄 Attempting with model: {model_name}...")
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(content)
                print(f"✅ Success with {model_name}!")
                return response.text
            except Exception as e:
                print(f"❌ Failed with {model_name}: {e}")
                last_error = e
                # Continue to next model
        
        # If all failed
        raise last_error

    except Exception as e:
        print(f"All models failed. Last error: {e}")
        return "👨‍🍳 ¡Ups! Estoy sobrecargado de pedidos (Límite de cuota alcanzado en Google). Intenta mañana cuando se recarguen mis energías."