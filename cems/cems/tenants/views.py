from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import College
from .forms import CollegeRegistrationForm


def tenant_home(request):
    """Landing page showing all active colleges with direct portal links."""
    colleges = College.objects.filter(status__in=['ACTIVE', 'TRIAL']).order_by('name')
    return render(request, 'tenants/home.html', {'colleges': colleges})


def register_college(request):
    """Super-admin registers a new college/tenant."""
    if not request.user.is_superuser:
        messages.error(request, 'Only super admins can register new colleges.')
        return redirect('home')

    if request.method == 'POST':
        form = CollegeRegistrationForm(request.POST)
        if form.is_valid():
            college = form.save()
            messages.success(request, f'College "{college.name}" registered successfully!')
            return redirect('admin_dashboard')
    else:
        form = CollegeRegistrationForm()
    return render(request, 'tenants/register_college.html', {'form': form})


# ─────────────────────────────────────────────────────────────────────────────
# COLLEGE PORTAL VIEWS  (each college gets its own URL)
# ─────────────────────────────────────────────────────────────────────────────

def college_portal(request, slug):
    """
    The dedicated portal page for a college.
    URL: /colleges/<slug>/
    Shows college branding, events, login & register options.
    """
    college = get_object_or_404(College, slug=slug, status__in=['ACTIVE', 'TRIAL'])
    # Set the session so all subsequent requests are scoped to this college
    request.session['college_id'] = str(college.id)
    request.session['college_name'] = college.name

    from events.models import Event
    upcoming_events = Event.objects.filter(
        college=college, status='PUBLISHED'
    ).order_by('date_time')[:6]

    return render(request, 'tenants/college_portal.html', {
        'college': college,
        'upcoming_events': upcoming_events,
    })

def college_login(request, slug):
    """Redirect to centralized login with college context."""
    return redirect('login_college_scoped', college_slug=slug)

def college_register(request, slug):
    """Redirect to centralized register with college context."""
    return redirect('register_college_scoped', college_slug=slug)
