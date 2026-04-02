import os
import django

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

if not User.objects.filter(username='superadmin').exists():
    user = User.objects.create_superuser('superadmin', 'super@auto.com', 'admin123')
    Profile.objects.get_or_create(user=user, role='ADMIN')
    print("✅ Super User created! Username: superadmin | Password: admin123")
else:
    print("✅ Super Admin already exists! (Username: superadmin)")
