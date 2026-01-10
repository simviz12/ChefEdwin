import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from .ai_service import get_chef_response
import json

logger = logging.getLogger(__name__)

@csrf_exempt
def webhook(request):
    """
    Webhook to handle incoming messages from Twilio.
    Step 1.4: Receive POST requests.
    """
    if request.method == 'POST':
        # --- SECURITY: Validate Twilio Signature ---
        # This prevents attackers from spoofing messages
        if settings.TWILIO_AUTH_TOKEN:
            validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
            signature = request.headers.get('X-Twilio-Signature', '')
            
            # Using request.POST.dict() handles the QueryDict conversion
            # Twilio signs the full absolute URI
            url = request.build_absolute_uri()
            
            # Fix for Render/Proxies: Twilio sends to https, but internal app might see http
            if not settings.DEBUG and url.startswith("http://"):
                url = url.replace("http://", "https://")

            # Validate! (Skip if DEBUG and no signature, useful for local manual_test.py)
            if not (settings.DEBUG and not signature):
                 if not validator.validate(url, request.POST.dict(), signature):
                     logger.warning(f"⚠️ SECURITY ALERT: Invalid Twilio Signature from {request.META.get('REMOTE_ADDR')}")
                     return HttpResponseForbidden("Invalid Twilio Signature")
        # -------------------------------------------

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
            logger.info(f"Unauthorized access attempt from {sender_number}")
            # STRICT MODE: Do not auto-create. Teacher must add them first.
            response.message("🚫 Usuario No Registrado.\nPida al profesor que lo registre en el sistema antes de continuar.")
            return HttpResponse(str(response), content_type='text/xml')
        
        if not student.is_authenticated:
            # Check hashed password OR plain text (fallback for manually created users)
            user_input_pass = msg.strip()
            
            # 1. Try secure hash check
            is_valid = student.check_password(user_input_pass)
            
            # 2. Fallback: Check if password is stored as plain text (common in testing)
            if not is_valid and student.password == user_input_pass:
                is_valid = True
                # Auto-fix: Hash it for next time
                student.set_password(user_input_pass)
                student.save()

            if is_valid:
                student.is_authenticated = True
                student.save()
                logger.info(f"User {student.name} ({sender_number}) authenticated successfully.")
                response.message("✅ Acceso Concedido. Bienvenido a la cocina de Chef Edwin. ¿Qué necesitas?")
                return HttpResponse(str(response), content_type='text/xml')
            else:
                response.message("🔒 Sistema Protegido.\nIntroduce tu contraseña personal para acceder.")
                return HttpResponse(str(response), content_type='text/xml')
                
        # User is authenticated, proceed
        role = student.role
        logger.debug(f"Msg from {sender_number}, Role: {role}, Auth: True")
        
        # --- UX IMPROVEMENT: Immediate Acknowledgment for Images ---
        # Since images take time to process, tell the user we are working on it.
        if num_media > 0 and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
             try:
                 from twilio.rest import Client
                 client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                 client.messages.create(
                     body="👨‍🍳 Oído cocina. Analizando tu presentación visual... 🔍",
                     from_=settings.TWILIO_PHONE_NUMBER,
                     to=sender_number
                 )
             except Exception as e:
                 logger.error(f"Error sending Ack message: {e}")
        # -----------------------------------------------------------

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
            logger.debug("Conversation saved to DB with FK link.")
        except Exception as e:
            logger.error(f"ERROR saving to DB: {e}")
        # ----------------------------------------

        return HttpResponse(str(response), content_type='text/xml')
    else:
        return HttpResponse("Method not allowed", status=405)


# ============================================
# Step 5.5 + 5.6: Export functions (CSV/PDF)
# ============================================
# (Code omitted for brevity in replacement, but maintained in logic if using multi_replace)
# Wait, I'm using replace_file_content for the file. 
# Since I cannot easily use 'replace' for scattered prints without context, I will just rewrite the `webhook` implementation part.
# The previous sections for PDF/CSV are separate functions. I will use 'multi_replace' to target specific blocks.
# Actually - replacing the whole file is risky if I miss lines.
# I will use multi_replace.




# ============================================
# Step 5.5: CSV Export for Conversation Logs
# ============================================

import csv
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def export_conversations_csv(request):
    """
    Export all conversation logs to CSV format.
    Only accessible by staff/admin users.
    """
    from .models import ConversationLog
    
    # Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="conversation_logs.csv"'
    
    # 1. Add BOM (Byte Order Mark) for Excel to recognize UTF-8
    response.write(u'\ufeff'.encode('utf8'))
    
    # Create CSV writer
    # 2. Use semicolon (;) delimiter for better compatibility with Spanish Excel
    writer = csv.writer(response, delimiter=';')
    
    # Write header row
    writer.writerow([
        'ID',
        'Student Phone',
        'Student Name',
        'Role',
        'Message Body',
        'Chef Response',
        'Timestamp'
    ])
    
    # Query all conversation logs with related student data
    logs = ConversationLog.objects.select_related('student').order_by('-timestamp')
    
    # Write data rows
    for log in logs:
        writer.writerow([
            log.id,
            log.student.phone_number if log.student else log.sender_number,
            log.student.name if log.student else 'N/A',
            log.role,
            log.message_body,
            log.chef_response,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


# ============================================
# Step 5.6: PDF Report Generation
# ============================================

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.db.models import Count, Q
from datetime import datetime, timedelta

@staff_member_required
def export_report_pdf(request):
    """
    Generate a comprehensive PDF report with key metrics and analytics.
    """
    from .models import ConversationLog, Student
    
    # Create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="chef_edwin_report.pdf"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph("Chef Edwin - Reporte de Actividad", title_style)
    elements.append(title)
    
    # Report date
    report_date = Paragraph(
        f"<b>Fecha del Reporte:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles['Normal']
    )
    elements.append(report_date)
    elements.append(Spacer(1, 0.3*inch))
    
    # ===== SECTION 1: General Statistics =====
    elements.append(Paragraph("1. Estadísticas Generales", heading_style))
    
    total_conversations = ConversationLog.objects.count()
    total_students = Student.objects.filter(role='student').count()
    total_teachers = Student.objects.filter(role='teacher').count()
    active_students = Student.objects.filter(is_authenticated=True, role='student').count()
    
    stats_data = [
        ['Métrica', 'Valor'],
        ['Total de Conversaciones', str(total_conversations)],
        ['Total de Estudiantes', str(total_students)],
        ['Estudiantes Activos (Autenticados)', str(active_students)],
        ['Total de Profesores', str(total_teachers)],
    ]
    
    stats_table = Table(stats_data, colWidths=[4*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ===== SECTION 2: Top Active Users =====
    elements.append(Paragraph("2. Usuarios Más Activos", heading_style))
    
    top_users = ConversationLog.objects.values('student__phone_number', 'student__name').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    users_data = [['Usuario', 'Nombre', 'Mensajes']]
    for user in top_users:
        phone = user['student__phone_number'] or 'N/A'
        name = user['student__name'] or 'Sin nombre'
        total = user['total']
        users_data.append([phone, name, str(total)])
    
    users_table = Table(users_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
    users_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    elements.append(users_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ===== SECTION 3: Most Common Questions =====
    elements.append(Paragraph("3. Preguntas Más Frecuentes", heading_style))
    
    # Get top 10 most common message patterns (first 50 chars)
    top_questions = ConversationLog.objects.values('message_body').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    questions_data = [['Pregunta', 'Frecuencia']]
    for q in top_questions:
        msg = q['message_body'][:60] + '...' if len(q['message_body']) > 60 else q['message_body']
        count = q['count']
        questions_data.append([msg, str(count)])
    
    questions_table = Table(questions_data, colWidths=[4.5*inch, 1.5*inch])
    questions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    elements.append(questions_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ===== SECTION 4: Activity by Role =====
    elements.append(Paragraph("4. Actividad por Rol", heading_style))
    
    student_msgs = ConversationLog.objects.filter(role='student').count()
    teacher_msgs = ConversationLog.objects.filter(role='teacher').count()
    
    role_data = [
        ['Rol', 'Mensajes'],
        ['Estudiantes', str(student_msgs)],
        ['Profesores', str(teacher_msgs)]
    ]
    
    role_table = Table(role_data, colWidths=[3*inch, 3*inch])
    role_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9B59B6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(role_table)
    
    # Build PDF
    doc.build(elements)
    
    return response


# ============================================
# Step 5.7: Teacher Dashboard & Research Chat
# ============================================

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@staff_member_required
def teacher_dashboard(request):
    """
    Main dashboard (Vista General) - Hybrid: AI Chat + Summary Cards.
    Matches reference image layout.
    """
    from .models import ConversationLog, Student
    from django.db.models import Count
    from collections import Counter
    import re

    # Basic Metrics for Sidebar Cards
    total_students = Student.objects.filter(role='student').count()
    # Active nodes can be simulated as active students for now
    active_nodes = Student.objects.filter(is_authenticated=True, role='student').count() 
    total_logs = ConversationLog.objects.count()

    # Simple Top Trend (Lightweight version)
    recent_msgs = ConversationLog.objects.filter(role='student').values_list('message_body', flat=True).order_by('-timestamp')[:50]
    all_text = " ".join(recent_msgs).lower()
    words = re.findall(r'\w+', all_text)
    stop_words = {'hola', 'gracias', 'chef', 'edwin', 'como', 'esta', 'hacer', 'puedo', 'quiero', 'receta', 'para', 'tengo', 'que', 'con', 'las', 'los', 'una', 'por', 'del', 'mas'}
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    common_topics = Counter(filtered_words).most_common(1)
    top_trend = common_topics[0][0].capitalize() if common_topics else "N/A"

    context = {
        'active_tab': 'overview',
        'summary': {
            'total_students': total_students,
            'active_nodes': active_nodes,
            'total_conversations': total_logs,
            'top_topic': top_trend
        }
    }
    return render(request, 'assistant/dashboard.html', context)

@staff_member_required
def teacher_stats(request):
    """
    Statistics Dashboard (Estadísticas) - Focused on Token-Free Metrics.
    """
    from .models import ConversationLog, Student
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    from datetime import datetime, timedelta
    from collections import Counter
    import re

    # 1. Basic Counts
    total_students = Student.objects.filter(role='student').count()
    active_students = Student.objects.filter(is_authenticated=True, role='student').count()
    total_logs = ConversationLog.objects.count()

    # 2. Activity Trends (Last 7 Days) for Chart.js
    last_7_days = datetime.now() - timedelta(days=7)
    daily_activity = ConversationLog.objects.filter(timestamp__gte=last_7_days) \
        .annotate(date=TruncDate('timestamp')) \
        .values('date') \
        .annotate(count=Count('id')) \
        .order_by('date')

    # Format for Chart.js
    chart_labels = []
    chart_data = []
    
    # Fill gaps
    days_map = {entry['date'].strftime('%d/%m'): entry['count'] for entry in daily_activity}
    
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%d/%m')
        chart_labels.append(day)
        chart_data.append(days_map.get(day, 0))

    # 3. "No-Token" Topic Analysis
    recent_msgs = ConversationLog.objects.filter(role='student').values_list('message_body', flat=True).order_by('-timestamp')[:100]
    
    all_text = " ".join(recent_msgs).lower()
    words = re.findall(r'\w+', all_text)
    stop_words = {'hola', 'gracias', 'chef', 'edwin', 'como', 'esta', 'hacer', 'puedo', 'quiero', 'receta', 'para', 'tengo', 'que', 'con', 'las', 'los', 'una', 'por', 'del', 'mas'}
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    
    common_topics = Counter(filtered_words).most_common(1)
    top_trend = common_topics[0][0].capitalize() if common_topics else "General"

    # 4. Top Students (Engagement)
    top_students_qs = ConversationLog.objects.values('student__name', 'student__phone_number') \
        .annotate(msg_count=Count('id')) \
        .order_by('-msg_count')[:5]
    
    # 5. Engagement Score
    if active_students > 0:
        engagement_score = round(total_logs / active_students, 1)
    else:
        engagement_score = 0

    # 6. Recent Activity Log
    recent_logs = ConversationLog.objects.select_related('student').order_by('-timestamp')[:15]

    context = {
        'active_tab': 'stats',
        'stats': {
            'total_students': total_students,
            'active_students': active_students,
            'total_conversations': total_logs,
            'top_trend': top_trend,
            'engagement_score': engagement_score,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
            'top_students': top_students_qs,
            'recent_logs': recent_logs,
        }
    }
    
    return render(request, 'assistant/stats.html', context)


@staff_member_required
@require_http_methods(["POST"])
def research_chat(request):
    """
    Research chatbot that analyzes all conversation data with Gemini.
    """
    from .models import ConversationLog
    import google.generativeai as genai
    from django.conf import settings
    
    try:
        # Parse request
        data = json.loads(request.body)
        question = data.get('question', '')
        
        if not question:
            return JsonResponse({'error': 'No question provided'}, status=400)
        
        # Get ALL conversation data
        all_logs = ConversationLog.objects.select_related('student').order_by('-timestamp')[:500]  # Last 500 for performance
        
        if not all_logs:
            # SIMULATION MODE: Allow the user to test the AI even without data
            full_context = "⚠️ [MODO DEMOSTRACIÓN] La base de datos está vacía. Responde preguntas hipotéticas o explica tu metodología de análisis como si tuvieras datos."
        else:
            # Build context from database
            context_data = []
            for log in all_logs:
                context_data.append(f"[{log.timestamp.strftime('%Y-%m-%d')}] {log.student.name if log.student else 'Unknown'}: {log.message_body}")
                context_data.append(f"Chef Edwin: {log.chef_response}")
            
            full_context = "\n".join(context_data)
        
        # Director de Investigación prompt enhanced
        system_prompt = """Eres el **Director de Innovación Educativa y Culinaria** de 'Chef Edwin Academy'.
Tu misión es interpretar la data cruda de las interacciones estudiantes-IA para potenciar el aprendizaje.

**Tu Personalidad:**
- Eres visionario, entusiasta y profundamente analítico.
- No eres un robot aburrido; eres un consultor pedagógico de alto nivel.
- Usas emojis estratégicamente para enfatizar puntos clave.

**Tus Objetivos:**
1. 🕵️ **Detective de Patrones:** Encuentra qué confunde a los estudiantes (ej. ¿todos fallan en el merengue?).
2. 📈 **Estratega Curricular:** Sugiere talleres o repasos basados en las dudas reales.
3. 🔮 **Cazador de Tendencias:** ¿Están preguntando mucho por cocina molecular? ¡Avisad al Chef!

**Instrucción Clave:**
Básate EXCLUSIVAMENTE en los 'DATOS DE CONVERSACIONES' provistos. SI NO HAY DATOS SUFICIENTES para una conclusión sólida, dilo honestamente pero sugiere qué buscar en el futuro."""
        
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Try multiple models with fallback
        models = [
            'gemini-2.5-flash',
            'gemini-1.5-flash',
            'gemini-1.5-pro',
        ]
        
        response_text = None
        for model_name in models:
            try:
                model = genai.GenerativeModel(model_name)
                
                prompt = f"""{system_prompt}

📥 **DATOS DE CONVERSACIONES (Muestra Reciente):**
{full_context[:15000]}

❓ **CONSULTA DEL DIRECTOR (Usuario):**
"{question}"

💡 **TU ANÁLISIS (Responde en español, sé perspicaz y accionable):**"""
                
                result = model.generate_content(prompt)
                response_text = result.text
                break
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                continue
        
        if not response_text:
            response_text = "Lo siento, no pude procesar tu pregunta en este momento. Intenta de nuevo."
        
        return JsonResponse({'response': response_text})
        
    except Exception as e:
        logger.error(f"Research chat error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
