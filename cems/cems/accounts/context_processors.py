def college_context(request):
    """
    Injects the current user's college into every template context.
    Now primarily driven by the Subdomain Middleware (request.college).
    """
    context = {'current_college': None, 'all_colleges': []}
    from tenants.models import College
    
    # Priority 1: Subdomain Context (Set by TenantMiddleware)
    if hasattr(request, 'college') and request.college:
        context['current_college'] = request.college
        
    # Priority 2: Fallback to Profile (If on central domain but logged in)
    if not context['current_college'] and request.user.is_authenticated:
        try:
            context['current_college'] = request.user.profile.college
        except: pass
        
    if request.user.is_authenticated and request.user.is_superuser:
        context['all_colleges'] = College.objects.filter(status='ACTIVE')
            
    return context

