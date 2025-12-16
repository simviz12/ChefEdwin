#!/usr/bin/env python
"""
Script para crear superusuario automáticamente en Render
Solo se ejecuta si no existe un superusuario
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chef_edwin.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Credenciales del superusuario (cámbialas antes de hacer push)
ADMIN_USERNAME = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
ADMIN_EMAIL = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@chefedwin.com')
ADMIN_PASSWORD = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'changeme123')

# Solo crear si no existe ningún superusuario
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD
    )
    print(f"✅ Superusuario '{ADMIN_USERNAME}' creado exitosamente")
else:
    print("ℹ️ Ya existe un superusuario, saltando creación")
