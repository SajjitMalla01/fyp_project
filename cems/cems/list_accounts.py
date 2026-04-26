import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

from django.contrib.auth.models import User
print("---ACCOUNTS---")
for u in User.objects.all():
    role = u.profile.role if hasattr(u, 'profile') else 'No profile'
    print(f"User: {u.username:<15} | Email: {u.email:<25} | Role: {role:<10} | Active: {u.is_active}")
