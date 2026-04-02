import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

try:
    from django.contrib.auth.models import User
    from accounts.models import Profile, EventComment
    from tenants.models import College
    from events.models import Event
    from registrations.models import Registration
    from django.utils import timezone
    from datetime import timedelta
except Exception as e:
    print(f"❌ Error importing models: {e}")
    exit(1)

print("🚀 Starting final CEMS configuration...")

try:
    # 1. Create professional colleges
    colleges_data = [
        {'name': 'Herald College Kathmandu', 'slug': 'herald-college', 'domain': 'heraldcollege.com', 'primary_color': '#111827', 'accent_color': '#3b82f6'},
        {'name': 'The British College', 'slug': 'british-college', 'domain': 'britishcollege.com', 'primary_color': '#dc2626', 'accent_color': '#1e3a8a'},
        {'name': 'Islington College', 'slug': 'islington-college', 'domain': 'islingtoncollege.edu.np', 'primary_color': '#0369a1', 'accent_color': '#0ea5e9'}
    ]

    colleges = []
    for c_data in colleges_data:
        college, created = College.objects.get_or_create(
            name=c_data['name'],
            defaults={'slug': c_data['slug'], 'domain': c_data['domain'], 'status': 'ACTIVE', 'primary_color': c_data['primary_color'], 'accent_color': c_data['accent_color']}
        )
        colleges.append(college)
        print(f"{'✅ Created' if created else 'ℹ️ Found'}: {college.name}")

    herald, british, islington = colleges

    # 2. Configure Super Admin
    super_admin, created = User.objects.get_or_create(
        username='superadmin',
        defaults={'email': 'superadmin@cems.com', 'is_staff': True, 'is_superuser': True, 'is_active': True}
    )
    super_admin.is_staff = True
    super_admin.is_superuser = True
    super_admin.is_active = True
    super_admin.set_password('admin123')
    super_admin.save()
    
    sp, _ = Profile.objects.get_or_create(user=super_admin)
    sp.role = 'ADMIN'
    sp.college = herald
    sp.save()
    print(f"✅ Superadmin Configured: admin123")

    # 3. Generate Content
    events_data = [
        {'title': 'AI Summit 2026', 'clg': herald, 'days': 5},
        {'title': 'Hackathon Elite', 'clg': british, 'days': 12},
        {'title': 'Career Fair', 'clg': herald, 'days': -2},
        {'title': 'Music Night', 'clg': british, 'days': 20},
        {'title': 'Tech Expo', 'clg': islington, 'days': 25},
    ]

    for ed in events_data:
        ev, created = Event.objects.get_or_create(
            title=ed['title'],
            defaults={'college': ed['clg'], 'date_time': timezone.now() + timedelta(days=ed['days']), 'venue': 'Main Hall', 'capacity': 200, 'status': 'PUBLISHED', 'created_by': super_admin}
        )
        if created:
            Registration.objects.get_or_create(event=ev, user=super_admin, status='REGISTERED')
            EventComment.objects.get_or_create(event=ev, user=super_admin, text="Great initiative!", is_pre_event=True)
            print(f"   + Event: {ev.title}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 ALL DONE!")
print("1. Superadmin: superadmin / admin123")
print("2. Run: python manage.py runserver")
