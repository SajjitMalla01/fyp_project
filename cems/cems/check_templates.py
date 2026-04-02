import os
import django
from django.conf import settings
from django.template.loader import get_template, render_to_string
from django.test import RequestFactory
from accounts.models import Profile, User
from events.models import Event
from tenants.models import College

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

def check_templates():
    errors = []
    # Just import everything to check if parsing fails
    import glob
    for filepath in glob.glob('templates/**/*.html', recursive=True):
        template_name = filepath.replace('templates\\', '').replace('\\', '/')
        if template_name.startswith('templates/'):
             template_name = template_name[10:]
             
        try:
             t = get_template(template_name)
             print(f"✅ {template_name} parsed successfully.")
        except Exception as e:
             errors.append((template_name, str(e)))
             print(f"❌ Error in {template_name}: {e}")

    if not errors:
        print("\nAll templates parsed successfully!")
    else:
        print("\nERRORS FOUND:")
        for t, e in errors:
            print(f"- {t}: {e}")

if __name__ == '__main__':
    check_templates()
