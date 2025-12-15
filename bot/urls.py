from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.bot_webhook, name='bot_webhook'),
]
