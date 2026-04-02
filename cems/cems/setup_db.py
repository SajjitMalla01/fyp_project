import os
import django
from django.core.management import call_command

# Setup django environment First
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

print("1. Creating database and applying migrations...")
try:
    # If django-tenants is active
    call_command("migrate_schemas", shared=True)
except Exception:
    # Fallback to standard Django migrate
    call_command("migrate")

# Now that the DB exists, create the superuser
from django.contrib.auth.models import User
from accounts.models import Profile

print("\n2. Creating super admin...")
if not User.objects.filter(username='superadmin').exists():
    user = User.objects.create_superuser('superadmin', 'super@auto.com', 'admin123')
    Profile.objects.get_or_create(user=user, role='ADMIN')
    print("✅ Database built and Super User created!")
    print("   Username: superadmin")
    print("   Password: admin123")
else:
    print("✅ Database is ready and Super Admin already exists! (Username: superadmin)")
