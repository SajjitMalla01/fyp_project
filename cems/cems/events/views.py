import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from events.forms import EventForm
from registrations.models import Registration
from accounts.models import Profile
from tenants.models import College
from django.contrib.auth.models import User


def home(request):
    # Tenant context is now automatically handled by TenantMiddleware
    college = getattr(request, 'college', None)
    
    # Optional: Logged-in user's profile as a fallback if on main domain
    if not college and request.user.is_authenticated:
        try:
            college = request.user.profile.college
        except: pass

    if college:
        events = Event.objects.filter(status='PUBLISHED', college=college).order_by('date_time')
    else:
        # For global landing page, show high-profile events across all sites
        events = Event.objects.filter(status='PUBLISHED').order_by('date_time')[:6]

    all_colleges = College.objects.filter(status='ACTIVE')
    
    # Global Stats
    stats = {
        'total_events': Event.objects.count(),
        'total_colleges': all_colleges.count(),
        'total_students': User.objects.count(), # Approximation
    }

    context = {
        'events': events, 
        'college': college, 
        'all_colleges': all_colleges,
        **stats
    }

    # Central site homepage (listing all events)
    return render(request, 'events/home.html', context)


@login_required
def admin_dashboard(request):
    # Role-based security gate
    try:
        if not (request.user.is_superuser or request.user.profile.role == 'ADMIN'):
            messages.error(request, "Permission Denied: Admins Only.")
            return redirect('student_dashboard')
    except:
        if not request.user.is_superuser: return redirect('home')

    now = timezone.now()
    # Scoping fix: Prioritize Portal context, fallback to profile
    college = getattr(request, 'college', None)
    if not college:
        try: college = request.user.profile.college
        except: pass

    event_qs = Event.objects.filter(college=college) if college else Event.objects.all()
    reg_qs   = Registration.objects.filter(event__college=college) if college else Registration.objects.all()

    # Optimized Stats
    stats = {
        'published':  event_qs.filter(status='PUBLISHED').count(),
        'pending':    event_qs.filter(status='PENDING').count(),
        'approved':   event_qs.filter(status='APPROVED').count(),
        'rejected':   event_qs.filter(status='REJECTED').count(),
        'total':      event_qs.count(),
        'total_regs': reg_qs.count(),
    }

    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_qs = User.objects.filter(profile__college=college) if college else User.objects.all()
    total_users = user_qs.count()

    try:
        from tenants.models import College
        total_colleges = College.objects.count() if request.user.is_superuser else 1
    except: total_colleges = 0

    recent_events = event_qs.annotate(reg_count=Count('registrations')).order_by('-created_at')[:8]
    pending_list  = event_qs.filter(status='PENDING').order_by('date_time').select_related('created_by')

    attended_count   = reg_qs.filter(status='ATTENDED').count()
    attendance_rate  = round((attended_count / stats['total_regs'] * 100) if stats['total_regs'] > 0 else 0)

    # 📊 HIGH-ACCURACY CALENDAR LOGIC
    monthly_labels, monthly_regs, monthly_events = [], [], []
    for i in range(5, -1, -1):
        # Calculate month start accurately without messy timedelta subtraction
        d = now.replace(day=1)
        for _ in range(i):
            d = (d - timedelta(days=1)).replace(day=1)
        
        m_start = d
        m_next  = (m_start + timedelta(days=32)).replace(day=1)
        
        monthly_labels.append(m_start.strftime('%b'))
        monthly_regs.append(reg_qs.filter(registered_at__gte=m_start, registered_at__lt=m_next).count())
        monthly_events.append(event_qs.filter(created_at__gte=m_start, created_at__lt=m_next).count())

    avg_regs = round(stats['total_regs'] / stats['total'], 1) if stats['total'] > 0 else 0
    
    from accounts.models import EventComment
    recent_comments = EventComment.objects.filter(event__college=college).order_by('-created_at')[:15] if college else EventComment.objects.all().order_by('-created_at')[:15]

    # 📊 Analytics Serialization
    monthly_data = {
        'labels': monthly_labels,
        'regs':   monthly_regs,
        'events': monthly_events
    }

    category_data = []
    for cat_code, cat_label in Event.CATEGORY_CHOICES:
        count = reg_qs.filter(event__category=cat_code).count()
        if count > 0:
            category_data.append({'label': cat_label, 'count': count})

    top_events = event_qs.annotate(
        reg_count=Count('registrations'),
        att_count=Count('registrations', filter=Q(registrations__status='ATTENDED'))
    ).order_by('-reg_count')[:10]

    performance_data = {
        'labels': [e.title[:20] for e in top_events],
        'regs':   [e.reg_count for e in top_events],
        'atts':   [e.att_count for e in top_events]
    }

    all_events = event_qs.annotate(reg_count=Count('registrations')).order_by('-date_time')
    attendance_log = reg_qs.select_related('user', 'event').order_by('-registered_at')[:50]

    from tenants.models import College
    colleges = College.objects.all()

    context = {
        **stats,
        'attendance_rate': attendance_rate,
        'total_users': total_users,
        'total_colleges': total_colleges,
        'recent_events': recent_events,
        'all_events': all_events,
        'pending_list': pending_list,
        'attendance_log': attendance_log,
        'monthly_data': json.dumps(monthly_data),
        'category_data_json': json.dumps(category_data),
        'performance_data_json': json.dumps(performance_data),
        'avg_regs': avg_regs,
        'recent_comments': recent_comments,
        'total_comments': recent_comments.count(),
        'college': college,
        'colleges': colleges,
    }
    return render(request, 'events/admin_dashboard.html', context)


@login_required
@require_POST
def add_comment(request, pk):
    event = get_object_or_404(Event, pk=pk)
    text = request.POST.get('text', '').strip()
    if text:
        from accounts.models import EventComment
        is_pre = timezone.now() < event.date_time
        EventComment.objects.create(event=event, user=request.user, text=text, is_pre_event=is_pre)
        messages.success(request, 'Your thought has been added to the community wall!')
    return redirect('event_detail', pk=pk)


@login_required
def staff_dashboard(request):
    # Role-based security gate: Staff or Admins only
    try:
        profile = request.user.profile
        if not (profile.role in ['STAFF', 'ADMIN'] or request.user.is_superuser):
            messages.error(request, "Permission Denied: Staff/Admin access only.")
            return redirect('student_dashboard')
    except:
        if not request.user.is_superuser: return redirect('home')

    now = timezone.now()
    # Scoping: Portal context first, fallback to profile
    college = getattr(request, 'college', None) or (request.user.profile.college if hasattr(request.user, 'profile') else None)

    if not college and not request.user.is_superuser:
        messages.error(request, 'No college context found. Please use a college portal link.')
        return redirect('home')

    # Data for the logged in staff member
    my_events = Event.objects.filter(created_by=request.user)

    stats = {
        'pending_events':   my_events.filter(status='PENDING').count(),
        'approved_events':  my_events.filter(status='APPROVED').count(),
        'published_events': my_events.filter(status='PUBLISHED').count(),
        'rejected_events':  my_events.filter(status='REJECTED').count(),
        'total_events':     my_events.count(),
    }

    recent_events = my_events.annotate(reg_count=Count('registrations')).order_by('-created_at')[:8]
    all_my_events = my_events.annotate(reg_count=Count('registrations')).order_by('-created_at')

    # Chart: registrations per event (top 6)
    top_for_chart = list(my_events.annotate(rc=Count('registrations')).order_by('-rc')[:6])
    reg_chart_labels = json.dumps([e.title[:18] + ('..' if len(e.title) > 18 else '') for e in top_for_chart])
    reg_chart_vals   = json.dumps([e.rc for e in top_for_chart])

    published_events_list = []
    for ev in my_events.filter(status='PUBLISHED').order_by('-date_time'):
        regs = Registration.objects.filter(event=ev).select_related('user').order_by('-registered_at')
        ev.active_reg_count    = regs.filter(status='REGISTERED').count()
        ev.recent_registrations = list(regs[:5])
        published_events_list.append(ev)

    total_participants = Registration.objects.filter(event__created_by=request.user).exclude(status='CANCELLED').count()

    # Calendar Data
    events_data = []
    for ev in all_my_events:
        events_data.append({
            'id': ev.pk, 'title': ev.title, 'date': ev.date_time.strftime('%Y-%m-%d'),
            'status': ev.status.lower(), 'emoji': getattr(ev, 'emoji', '📅'), 'grad': getattr(ev, 'gradient', 'g-blue'),
        })

    from accounts.models import EventComment
    recent_comments = EventComment.objects.filter(event__college=college).order_by('-created_at')[:15]

    context = {
        **stats,
        'recent_events':         recent_events,
        'all_my_events':         all_my_events,
        'reg_chart_labels':      reg_chart_labels,
        'reg_chart_vals':        reg_chart_vals,
        'published_events_list': published_events_list,
        'total_participants':    total_participants,
        'events_data':           json.dumps(events_data),
        'recent_comments':       recent_comments,
        'total_comments':        recent_comments.count(),
        'status_breakdown':      json.dumps([stats['pending_events'], stats['approved_events'], stats['published_events'], stats['rejected_events']]),
    }
    return render(request, 'events/staff_dashboard.html', context)


@login_required
def student_dashboard(request):
    """Student portal: registered events, calendar, feedback wall."""
    user = request.user
    from registrations.models import Registration
    from django.db.models import Count
    
    regs = Registration.objects.filter(user=user).select_related('event')
    
    registered_events = [r.event for r in regs if r.status == 'REGISTERED']
    attended_events   = [r.event for r in regs if r.status == 'ATTENDED']
    
    # Calendar data (only events they registered for)
    events_data = []
    for r in regs:
        if r.status in ['REGISTERED', 'ATTENDED']:
            ev = r.event
            events_data.append({
                'id': ev.pk,
                'title': ev.title,
                'date': ev.date_time.strftime('%Y-%m-%d'),
                'status': 'published' if r.status == 'ATTENDED' else 'pending',
                'emoji': getattr(ev, 'emoji', '🎉'),
                'grad': getattr(ev, 'gradient', 'g-blue'),
            })

    from accounts.models import EventComment
    # Priority for side-by-side context
    target_college = None
    cid = request.GET.get('college_id') or request.session.get('college_id')
    if cid:
        from tenants.models import College
        try:
            target_college = College.objects.get(id=cid)
        except: pass
    
    if not target_college:
        try:
            target_college = user.profile.college
        except: pass

    my_comments = EventComment.objects.filter(user=user).order_by('-created_at')[:10]
    if target_college:
        college_wall = EventComment.objects.filter(event__college=target_college).order_by('-created_at')[:15]
    else:
        college_wall = EventComment.objects.none()

    context = {
        'registered_count': len(registered_events),
        'attended_count':   len(attended_events),
        'total_events':     len(registered_events) + len(attended_events),
        'upcoming_events':  [e for e in registered_events if e.date_time > timezone.now()],
        'events_data':      json.dumps(events_data),
        'recent_comments':  college_wall,
        'my_comments':      my_comments,
        'total_comments':   my_comments.count(),
    }
    return render(request, 'events/student_dashboard.html', context)


@login_required
def event_list(request):
    college = getattr(request, 'college', None) or (request.user.profile.college if hasattr(request.user, 'profile') else None)

    try:
        profile = request.user.profile
        base_qs = Event.objects.filter(college=college) if college else Event.objects.all()
        if profile.is_admin or request.user.is_superuser:
            events = base_qs.order_by('-created_at')
        elif profile.is_staff:
            events = base_qs.filter(created_by=request.user).order_by('-created_at')
        else:
            events = base_qs.filter(status='PUBLISHED').order_by('date_time')
    except Exception:
        if request.user.is_superuser:
            events = Event.objects.all().order_by('-created_at')
        else:
            events = Event.objects.filter(status='PUBLISHED').order_by('date_time')
    return render(request, 'events/event_list.html', {'events': events, 'college': college})


@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    spots_left = event.spots_left()
    user_registration = None
    try:
        user_registration = Registration.objects.get(user=request.user, event=event)
    except Registration.DoesNotExist:
        pass
    return render(request, 'events/event_detail.html', {
        'event':             event,
        'spots_left':        spots_left,
        'user_registration': user_registration,
    })


@login_required
def event_create(request):
    try:
        profile = request.user.profile
        if not (profile.is_staff or profile.is_admin or request.user.is_superuser):
            messages.error(request, 'Only staff can create events.')
            return redirect('event_list')
    except Exception:
        if not request.user.is_superuser:
            messages.error(request, 'Permission denied.')
            return redirect('event_list')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            
            # Use subdomain/portal context first, fallback to profile
            active_college = getattr(request, 'college', None)
            if not active_college:
                try:
                    active_college = request.user.profile.college
                except: pass
            
            event.college = active_college
            
            # Superadmins and College Admins can auto-approve their own events
            is_admin = False
            try:
                is_admin = request.user.profile.role == 'ADMIN'
            except: pass
            
            if request.user.is_superuser or is_admin:
                event.status = 'PUBLISHED'
                msg = f'"{event.title}" has been published successfully!'
            else:
                event.status = 'PENDING'
                msg = f'"{event.title}" has been submitted for review. It will appearing on the portal once approved.'
                
            event.save()
            messages.success(request, msg)
            from accounts.views import _redirect_by_role
            return _redirect_by_role(request.user)
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form, 'title': 'Create New Event'})


@login_required
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    try:
        if not (event.created_by == request.user or request.user.is_superuser or getattr(request.user.profile, 'is_admin', False)):
            messages.error(request, 'Permission denied.')
            return redirect('event_detail', pk=pk)
    except Exception:
        if not (event.created_by == request.user or request.user.is_superuser):
            messages.error(request, 'Permission denied.')
            return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{event.title}" updated.')
            return redirect('event_detail', pk=pk)
    else:
        form = EventForm(instance=event)
    return render(request, 'events/event_form.html', {'form': form, 'title': f'Edit: {event.title}'})


@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    try:
        if not (event.created_by == request.user or request.user.is_superuser or getattr(request.user.profile, 'is_admin', False)):
            messages.error(request, 'Permission denied.')
            return redirect('event_detail', pk=pk)
    except Exception:
        if not (event.created_by == request.user or request.user.is_superuser):
            messages.error(request, 'Permission denied.')
            return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, f'"{title}" deleted.')
        return redirect('event_list')
    return render(request, 'events/event_confirm_delete.html', {'event': event})


@login_required
def approve_event(request, pk):
    try:
        if not (request.user.is_superuser or getattr(request.user.profile, 'is_admin', False)):
            messages.error(request, 'Only admins can approve events.')
            return redirect('admin_dashboard')
    except Exception:
        if not request.user.is_superuser:
            return redirect('home')

    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.status = 'APPROVED'
        event.save()
        messages.success(request, f'"{event.title}" approved.')
        return redirect('admin_dashboard')
    return render(request, 'events/approve_confirm.html', {'event': event})


@login_required
def publish_event(request, pk):
    try:
        if not (request.user.is_superuser or getattr(request.user.profile, 'is_admin', False)):
            messages.error(request, 'Only admins can publish events.')
            return redirect('admin_dashboard')
    except Exception:
        if not request.user.is_superuser:
            return redirect('home')

    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.status = 'PUBLISHED'
        event.save()
        messages.success(request, f'"{event.title}" is now live.')
        return redirect('admin_dashboard')
    return render(request, 'events/publish_confirm.html', {'event': event})


@login_required
@require_POST
def update_event_status(request, pk):
    try:
        event = get_object_or_404(Event, pk=pk)
        
        # Permission check
        is_global_admin = request.user.is_superuser
        college_admin   = False
        try:
            profile = request.user.profile
            college_admin = (profile.college == event.college and profile.role == 'ADMIN')
        except: pass
        
        if not (is_global_admin or college_admin):
            return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

        data = json.loads(request.body)
        status = data.get('status', '').upper()
        reason = data.get('reason', '')

        if status not in {'APPROVED', 'REJECTED', 'PUBLISHED', 'PENDING'}:
            return JsonResponse({'success': False, 'message': f'Invalid status: {status}'})
            
        event.status = status
        # If rejecting, append the reason to description for now (or a new field if added)
        if status == 'REJECTED' and reason:
            event.description = f"{event.description}\n\n[ADMIN FEEDBACK]: {reason}"
            
        event.save()
        return JsonResponse({'success': True, 'message': f'Status updated to {status}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
