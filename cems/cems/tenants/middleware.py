from tenants.models import College
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import connection

class TenantMiddleware:
    """
    Middleware to determine the tenant (College) based on either the subdomain OR the path.
    
    Priority:
    1. Subdomain: herald.localhost:8000 -> request.college = Herald College
    2. Path: localhost:8000/colleges/herald-college/ -> request.college = Herald College
    3. Central Hub: localhost:8000 -> request.college = None
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        host = request.get_host().split(':')[0].lower()
        request.college = None
        
        # 1. Detection by Subdomain (e.g., herald.localhost)
        # Assuming main host is localhost or 127.0.0.1 or a production domain
        main_hosts = ['localhost', '127.0.0.1', 'cems.app'] 
        if host not in main_hosts:
            # Extract subdomain
            subdomain = host.split('.')[0]
            try:
                from tenants.models import College
                request.college = College.objects.filter(slug=subdomain, status='ACTIVE').first()
            except: pass

        # 2. Detection by Path Prefix (fallback if not already detected by subdomain)
        if not request.college and path.startswith('/colleges/'):
            parts = [p for p in path.split('/') if p]
            if len(parts) >= 2:
                from tenants.models import College
                try:
                    request.college = College.objects.get(slug=parts[1], status='ACTIVE')
                except: pass

        response = self.get_response(request)
        return response
