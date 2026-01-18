
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chef_edwin.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.getenv('DJANGO_ADMIN_USER', 'chef')
password = os.getenv('DJANGO_ADMIN_PASSWORD', 'chef123')
email = os.getenv('DJANGO_ADMIN_EMAIL', 'admin@chefedwin.com')

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
