import os
import django
import sys
import uuid

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

from tenants.models import College

def create_colleges():
    # Herald College Kathmandu
    h_name = "Herald College Kathmandu"
    h_slug = "herald-college"
    h_domain = "heraldcollege.edu.np"
    
    # British College
    b_name = "The British College"
    b_slug = "british-college"
    b_domain = "thebritishcollege.edu.np"
    
    colleges = [
        {
            'name': h_name,
            'slug': h_slug,
            'domain': h_domain,
            'primary_color': '#2563eb',
            'accent_color': '#7c3aed',
            'address': 'Durbarmarg, Kathmandu, Nepal',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/8d/Herald_College_Kathmandu_logo.png/220px-Herald_College_Kathmandu_logo.png'
        },
        {
            'name': b_name,
            'slug': b_slug,
            'domain': b_domain,
            'primary_color': '#dc2626',
            'accent_color': '#111827',
            'address': 'Chakupat, Lalitpur, Nepal',
            'logo_url': 'https://www.thebritishcollege.edu.np/images/tbc-logo.png'
        }
    ]
    
    for c_data in colleges:
        college, created = College.objects.get_or_create(
            slug=c_data['slug'],
            defaults={
                'name': c_data['name'],
                'domain': c_data['domain'],
                'primary_color': c_data['primary_color'],
                'accent_color': c_data['accent_color'],
                'address': c_data['address'],
                'logo_url': c_data['logo_url'],
                'status': 'ACTIVE'
            }
        )
        if created:
            print(f"Created college: {college.name}")
        else:
            print(f"College already exists: {college.name}")

if __name__ == '__main__':
    create_colleges()
