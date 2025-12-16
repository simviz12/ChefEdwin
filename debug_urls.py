
import os
import django
from django.urls import get_resolver

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chef_edwin.settings')
django.setup()

print("Resolving URLs...")
resolver = get_resolver()
for pattern in resolver.url_patterns:
    print(pattern)
    if hasattr(pattern, 'url_patterns'):
        for sub in pattern.url_patterns:
            print(f"  -> {sub}")
