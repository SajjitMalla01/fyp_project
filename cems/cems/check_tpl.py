import os
import django
from django.template.loader import get_template

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cems.settings')
django.setup()

for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            template_name = os.path.relpath(path, 'templates').replace('\\', '/')
            try:
                get_template(template_name)
            except Exception as e:
                print(f"Error in {template_name}: {e}")
