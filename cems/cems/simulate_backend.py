import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import Event
from registrations.models import Registration

try:
    admin = User.objects.get(username='demo_admin')
    staff = User.objects.get(username='demo_staff')
    stud = User.objects.get(username='demo_stud')

    print("========================================")
    print("      CEMS AUTOMATED FLOW START         ")
    print("========================================")

    # 1. Check for the event staff just created
    event = Event.objects.filter(created_by=staff, status='PENDING').last()
    
    if not event:
        print("Creating event programmatically as staff...")
        from tenants.models import College
        college = College.objects.first()
        from django.utils import timezone
        import datetime
        event = Event.objects.create(
            title='Agentic AI Revolution',
            description='A fully automated simulation of event creation workflows driven by an LLM backend.',
            date_time=timezone.now() + datetime.timedelta(days=1),
            venue='Virtual Matrix Hub',
            capacity=300,
            category='technology',
            created_by=staff,
            college=college,
            status='PENDING'
        )
    
    print(f"[Staff] Created Event: '{event.title}' (ID: {event.id})")
    print(f"[Staff] Event Status: {event.status}")
    print("----------------------------------------")

    # 2. Admin action
    print(f"[Admin] Reviewing pending event {event.title}...")
    event.status = 'PUBLISHED'
    event.save()
    print(f"[Admin] Event '{event.title}' is now approved and PUBLISHED.")
    print("----------------------------------------")

    # 3. Student Registration
    print(f"[Student] {stud.username} is viewing the event...")
    print(f"[Student] Registering for {event.title}...")
    reg, created = Registration.objects.get_or_create(user=stud, event=event, defaults={'status': 'REGISTERED'})
    print(f"[System] Registration created successfully! Ticket ID: {reg.id} - Status: {reg.status}")
    
    print("========================================")
    print(" * FULL FLOW COMPLETED SUCCESSFULLY! * ")
    print(f" View the event live at: http://localhost:8000/events/{event.id}/")
    print(f" View your tickets at: http://localhost:8000/registrations/dashboard/")
    print("========================================")

except Exception as e:
    print("Error executing flow:", e)
