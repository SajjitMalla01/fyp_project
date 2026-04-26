import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'cems.settings'
django.setup()

from django.template.loader import get_template
from django.template.exceptions import TemplateSyntaxError
from django.core.management import call_command
from io import StringIO

print("=" * 60)
print("CEMS FULL AUDIT REPORT")
print("=" * 60)

# 1: Django system check
print("\n[1] Django System Check...")
out = StringIO()
try:
    call_command('check', stdout=out, stderr=out)
    print("   PASS:", out.getvalue().strip())
except Exception as e:
    print("   FAIL:", e)

# 2: Template check
print("\n[2] Template Syntax Check...")
import os as _os
root = 'templates'
errs = []
ok = 0
for dp, dn, fs in _os.walk(root):
    for f in fs:
        if not f.endswith('.html'): continue
        path = _os.path.join(dp, f)
        name = _os.path.relpath(path, root).replace('\\', '/')
        try:
            get_template(name)
            ok += 1
        except Exception as e:
            errs.append((name, str(e)))

if errs:
    for name, err in errs:
        print(f"   FAIL: {name} -> {err}")
else:
    print(f"   PASS: All {ok} templates OK")

# 3: Import check for all views
print("\n[3] Views Import Check...")
for app in ['events.views', 'accounts.views', 'registrations.views', 'tenants.views']:
    try:
        __import__(app)
        print(f"   PASS: {app}")
    except Exception as e:
        print(f"   FAIL: {app} -> {e}")

# 4: Model field issues
print("\n[4] Model Consistency Check...")
from events.models import Event
from registrations.models import Registration
from accounts.models import Profile
from tenants.models import College

for model, name in [(Event, 'Event'), (Registration, 'Registration'), (Profile, 'Profile'), (College, 'College')]:
    try:
        c = model.objects.count()
        print(f"   PASS: {name} ({c} records)")
    except Exception as e:
        print(f"   FAIL: {name} -> {e}")

# 5: URL resolution check
print("\n[5] URL Resolution Check...")
from django.test import RequestFactory
from django.urls import reverse, NoReverseMatch

urls_to_check = [
    'home', 'event_list', 'event_create',
    'admin_dashboard', 'staff_dashboard', 'student_dashboard',
    'login', 'logout', 'register', 'profile',
    'verify_email', 'resend_verification',
    'scanner', 'my_registrations',
    'tenant_home', 'register_college',
]
for url in urls_to_check:
    try:
        reverse(url)
        print(f"   PASS: {url}")
    except NoReverseMatch as e:
        print(f"   FAIL: {url} -> {e}")

# 6: Registration model status choices
print("\n[6] Registration Status Choices...")
statuses = [s[0] for s in Registration._meta.get_field('status').choices]
print(f"   Status options: {statuses}")

print("\n" + "=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)
