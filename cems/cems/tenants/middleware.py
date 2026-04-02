from tenants.models import College
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import connection

class TenantMiddleware:
    """
    Middleware to determine the tenant (College) based on the subdomain.
    Sets 'request.college' and dynamically prefixes the session cookie.
    
    Example: 
    - herald.localhost:8000 -> request.college = Herald College
    - localhost:8000        -> request.college = None (Central Hub)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        request.college = None
        
        # Simple extraction for branding context
        if path.startswith('/colleges/'):
            parts = [p for p in path.split('/') if p]
            if len(parts) >= 2:
                from .models import College
                try:
                    request.college = College.objects.get(slug=parts[1], status__in=['ACTIVE', 'TRIAL'])
                except: pass

        response = self.get_response(request)
        return response
