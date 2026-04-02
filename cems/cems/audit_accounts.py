import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

print("Registered Accounts:")
print("-" * 50)
for user in User.objects.all():
    try:
        role = user.profile.role
        college = user.profile.college.name if user.profile.college else "None"
    except:
        role = "N/A"
        college = "N/A"
    print(f"User: {user.username:<15} | Email: {user.email:<25} | Role: {role:<10} | Super: {user.is_superuser:<5} | College: {college}")

superadmin = User.objects.filter(username='superadmin').first()
if superadmin:
    print("\nSuperadmin Found!")
    print(f"Is Superuser: {superadmin.is_superuser}")
    print(f"Is Staff: {superadmin.is_staff}")
else:
    print("\nSuperadmin NOT FOUND.")
