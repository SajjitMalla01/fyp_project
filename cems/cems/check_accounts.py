import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

print(f"{'Username':<15} | {'Email':<25} | {'Role':<10} | {'College':<20} | {'Staff':<5} | {'Super'}")
print("-" * 100)

for u in User.objects.all():
    try:
        p = u.profile
        college = p.college.name if p.college else "None"
        role = p.role
    except:
        college = "N/A"
        role = "N/A"
    
    print(f"{u.username:<15} | {u.email:<25} | {role:<10} | {college:<20} | {u.is_staff:<5} | {u.is_superuser}")
