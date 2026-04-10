import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, EmailVerification
from tenants.models import College
from django.utils import timezone

def rebuild():
    print("--- Initializing CEMS Golden Accounts ---")
    
    # 1. Fetch Tenants
    herald = College.objects.filter(slug='herald-college').first()
    british = College.objects.filter(slug='british-college').first()
    
    if not herald or not british:
        print("Error: Essential colleges (herald-college, british-college) not found. Run setup_colleges.py first.")
        return

    accounts = [
        {
            'username': 'cems_admin',
            'email': 'np03cs4a230357@heraldcollege.edu.np',
            'password': 'CemsPass123!',
            'role': 'ADMIN',
            'college': herald,
            'is_superuser': True
        },
        {
            'username': 'cems_staff',
            'email': 'np03cs4a230357@heraldcollege.edu.np',
            'password': 'CemsPass123!',
            'role': 'STAFF',
            'college': herald,
            'is_superuser': False
        },
        {
            'username': 'cems_student',
            'email': 'np03cs4a230357@heraldcollege.edu.np',
            'password': 'CemsPass123!',
            'role': 'STUDENT',
            'college': british, # Test cross-college login
            'is_superuser': False
        }
    ]

    for data in accounts:
        # Clean up existing
        User.objects.filter(username=data['username']).delete()
        
        # Create User
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        user.is_superuser = data['is_superuser']
        user.is_staff = data['is_superuser']
        user.save()
        
        # Create Profile
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = data['role']
        profile.college = data['college']
        profile.save()
        
        # Force Email Verification
        EmailVerification.objects.update_or_create(
            user=user,
            defaults={'is_verified': True, 'expires_at': timezone.now() + timezone.timedelta(days=365)}
        )
        
        print(f"[OK] Created {data['role']}: {data['username']} (Tenant: {data['college'].name})")

    print("\nALL ACCOUNTS ARE READY.")
    print("Password for all: CemsPass123!")

if __name__ == "__main__":
    rebuild()
