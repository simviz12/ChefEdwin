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
# Credenciales quemadas para asegurar acceso en demo
ADMIN_USERNAME = 'chef'
ADMIN_EMAIL = 'admin@chefedwin.com'
ADMIN_PASSWORD = 'chef123'

# Buscar si existe el usuario, si no crearlo
try:
    user = User.objects.get(username=ADMIN_USERNAME)
    print(f"ℹ️ Usuario '{ADMIN_USERNAME}' ya existe. Asegurando permisos...")
    if not user.is_superuser:
        user.is_superuser = True
        user.is_staff = True
    user.set_password(ADMIN_PASSWORD)
    user.save()
    print(f"✅ Usuario '{ADMIN_USERNAME}' actualizado correctamente.")
except User.DoesNotExist:
    # Crear nuevo si no existe
    User.objects.create_superuser(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD
    )
    print(f"✅ Superusuario '{ADMIN_USERNAME}' creado exitosamente")
