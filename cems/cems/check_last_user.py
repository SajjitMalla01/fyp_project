import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

from django.contrib.auth.models import User

user = User.objects.all().order_by('-id').first()
if user:
    print(f"User: {user.username}")
    print(f"Email: {user.email}")
else:
    print("No users found.")
