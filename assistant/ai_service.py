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

**Memoria Histórica:** Tienes acceso y debes utilizar los registros de las interacciones y recetas culinarias pasadas de ESTE usuario (el estudiante que te está chateando) para ofrecer ayuda personalizada. Por ejemplo, si te preguntan por 'la carbonara de hace un mes', debes recuperar los detalles.

**Generación de Recetas:** Si el estudiante pide una receta y no hay una específica en su historial, ¡CRÉALA! Proponle recetas deliciosas, económicas y fáciles de hacer, ideales para estudiantes.

**Restricciones de Privacidad y Alcance (NO NEGOCIABLES):**
1.  **NUNCA** debes acceder, mencionar, o discutir datos académicos (notas, asistencia, cursos).
2.  **NUNCA** debes mencionar datos, conversaciones, o información de otros estudiantes.
3.  **Tono:** Amigable, entusiasta, de apoyo e instructivo.
"""

def get_chef_response(user_message, image_url=None, role='student'):
    """
    Generates a response using Google Gemini, selecting the prompt based on role.
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Switching to gemini-2.5-flash-lite (Last hope for fresh quota)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Select prompt based on role
        if role == 'teacher':
            system_prompt = PROMPT_TEACHER
        else:
            system_prompt = PROMPT_STUDENT
        
        # Prepare content list (Step 3.2 & 3.3)
        content = [f"{system_prompt}\n\nPREGUNTA DEL USUARIO:\n{user_message}"]
        
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
                
        response = model.generate_content(content)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return "👨‍🍳 ¡Ups! Se me quemó el agua. Hubo un error procesando tu solicitud. Intenta de nuevo."
