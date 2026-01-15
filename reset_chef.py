
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chef_edwin.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = 'chef'
password = 'chef123'
email = 'admin@chefedwin.com'

try:
    user = User.objects.get(username=username)
    print(f"Usuario {username} encontrado. Actualizando contraseña...")
    user.set_password(password)
    user.save()
    print("✅ Contraseña actualizada.")
except User.DoesNotExist:
    print(f"Usuario {username} no existe. Creando...")
    User.objects.create_superuser(username, email, password)
    print("✅ Superusuario creado.")
