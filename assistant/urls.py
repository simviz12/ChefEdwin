from django.urls import path
from django.http import HttpResponse
from . import views

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
    path('export/csv/', views.export_conversations_csv, name='export_csv'),
    path('export/pdf/', views.export_report_pdf, name='export_pdf'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('research-chat/', views.research_chat, name='research_chat'),
    path('ping/', lambda request: HttpResponse('pong'), name='ping'),
]
