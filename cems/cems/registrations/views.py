from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from events.models import Event
from .models import Registration


@login_required
def registrations_old(request):
    try:
        if not request.user.profile.is_student:
            messages.error(request, 'Access denied.')
            return redirect('home')
    except Exception:
        messages.error(request, 'Profile not found.')
        return redirect('home')

    now = timezone.now()

    all_registrations = (
        Registration.objects
        .filter(user=request.user)
        .select_related('event')
        .order_by('-registered_at')
    )

    total_registered = all_registrations.filter(status='REGISTERED').count()
    upcoming_count   = all_registrations.filter(status='REGISTERED', event__date_time__gte=now).count()
    attended_count   = all_registrations.filter(status='ATTENDED').count()

    my_upcoming = list(
        all_registrations.filter(status='REGISTERED', event__date_time__gte=now)
        .order_by('event__date_time')[:5]
    )

    registered_event_ids = list(
        all_registrations.exclude(status='CANCELLED').values_list('event_id', flat=True)
    )

    candidate_events = list(
        Event.objects
        .filter(status='PUBLISHED', date_time__gte=now)
        .exclude(id__in=registered_event_ids)
        .order_by('date_time')
    )

    available_events = [e for e in candidate_events if not e.is_full()]
    available_count  = len(available_events)

    context = {
        'total_registered':  total_registered,
        'upcoming_count':    upcoming_count,
        'attended_count':    attended_count,
        'my_upcoming':       my_upcoming,
        'all_registrations': all_registrations,
        'available_events':  available_events,
        'available_count':   available_count,
    }
    return render(request, 'registrations/student_dashboard.html', context)


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    try:
        if not request.user.profile.is_student:
            messages.error(request, 'Only students can register for events.')
            return redirect('event_detail', pk=event_id)
    except Exception:
        messages.error(request, 'Permission denied.')
        return redirect('event_detail', pk=event_id)

    if event.status != 'PUBLISHED':
        messages.error(request, 'This event is not open for registration.')
        return redirect('event_detail', pk=event_id)

    existing = Registration.objects.filter(user=request.user, event=event).first()

    if existing:
        if existing.status == 'CANCELLED':
            if event.is_full():
                messages.error(request, 'Sorry, this event is now full.')
                return redirect('event_detail', pk=event_id)
            if request.method == 'POST':
                existing.status = 'REGISTERED'
                existing.registered_at = timezone.now()
                existing.save()
                messages.success(request, f'You\'re registered for "{event.title}"!')
                return redirect('student_dashboard')
            return render(request, 'registrations/register_confirm.html', {
                'event': event, 'spots_left': event.spots_left()
            })
        else:
            messages.info(request, 'You are already registered for this event.')
            return redirect('event_detail', pk=event_id)

    if event.is_full():
        messages.error(request, 'Sorry, this event is full.')
        return redirect('event_detail', pk=event_id)

    if request.method == 'POST':
        Registration.objects.create(user=request.user, event=event, status='REGISTERED')
        messages.success(request, f'Successfully registered for "{event.title}"!')
        return redirect('student_dashboard')

    return render(request, 'registrations/register_confirm.html', {
        'event': event, 'spots_left': event.spots_left()
    })


@login_required
def cancel_registration(request, registration_id):
    reg = get_object_or_404(Registration, pk=registration_id, user=request.user)

    if reg.status == 'CANCELLED':
        messages.info(request, 'This registration is already cancelled.')
        return redirect('my_registrations')

    if request.method == 'POST':
        reg.status = 'CANCELLED'
        reg.save()
        messages.success(request, f'Registration for "{reg.event.title}" cancelled.')
        return redirect('student_dashboard')

    return render(request, 'registrations/cancel_confirm.html', {'registration': reg})


@login_required
def my_registrations(request):
    registrations = (
        Registration.objects
        .filter(user=request.user)
        .select_related('event')
        .order_by('-registered_at')
    )
    return render(request, 'registrations/my_registrations.html', {'registrations': registrations})


@login_required
def participant_list(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    try:
        if not (request.user.is_superuser or request.user.profile.is_staff or request.user.profile.is_admin):
            messages.error(request, 'Access denied.')
            return redirect('event_detail', pk=event_id)
    except Exception:
        messages.error(request, 'Access denied.')
        return redirect('event_detail', pk=event_id)

    regs = (
        Registration.objects
        .filter(event=event)
        .select_related('user', 'user__profile')
        .order_by('-registered_at')
    )
    return render(request, 'registrations/participant_list.html', {
        'event':         event,
        'registrations': regs,
        'active':        regs.filter(status='REGISTERED').count(),
        'attended':      regs.filter(status='ATTENDED').count(),
        'cancelled':     regs.filter(status='CANCELLED').count(),
        'total':         regs.count(),
    })
