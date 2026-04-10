from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from events.models import Event
from registrations.models import Registration


def _send_confirmation_email(registration):
    """
    Sends a high-fidelity confirmation email to the student upon successful registration.
    """
    event = registration.event
    user = registration.user
    
    subject = f'Registration Confirmed: {event.title}'
    context = {
        'user': user,
        'event': event,
        'registration': registration,
        'college': event.college
    }
    
    html_message = render_to_string('emails/registration_success.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        print(f"Email failed: {e}")


@login_required
def register_event(request, event_id):
    """Handles event registration with support for moderated approval."""
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
                status = 'PENDING' if event.requires_approval else 'REGISTERED'
                existing.status = status
                existing.registered_at = timezone.now()
                existing.save()
                
                if status == 'REGISTERED':
                    _send_confirmation_email(existing)
                    messages.success(request, f"Successfully registered for {event.title}!")
                else:
                    messages.info(request, "Registration submitted. This event requires admin approval.")
                return redirect('student_dashboard')
            return render(request, 'registrations/register_confirm.html', {
                'event': event, 'spots_left': event.spots_left()
            })
        else:
            messages.info(request, f"You have already submitted a registration for this event (Status: {existing.status}).")
            return redirect('event_detail', pk=event_id)

    if event.is_full():
        messages.error(request, 'Sorry, this event is full.')
        return redirect('event_detail', pk=event_id)

    if request.method == 'POST':
        status = 'PENDING' if event.requires_approval else 'REGISTERED'
        reg = Registration.objects.create(user=request.user, event=event, status=status)
        
        if status == 'REGISTERED':
            _send_confirmation_email(reg)
            messages.success(request, f'Successfully registered for "{event.title}"!')
        else:
            messages.info(request, "Registration submitted. This event requires admin approval.")
        return redirect('student_dashboard')

    return render(request, 'registrations/register_confirm.html', {
        'event': event, 'spots_left': event.spots_left()
    })


@login_required
def cancel_registration(request, registration_id):
    reg = get_object_or_404(Registration, pk=registration_id, user=request.user)

    if reg.status == 'CANCELLED':
        messages.info(request, 'This registration is already cancelled.')
        return redirect('student_dashboard')

    if request.method == 'POST':
        reg.status = 'CANCELLED'
        reg.save()
        messages.success(request, f'Registration for "{reg.event.title}" cancelled.')
        return redirect('student_dashboard')

    return render(request, 'registrations/cancel_confirm.html', {'registration': reg})


@login_required
def my_registrations(request):
    """User-facing view of their own registrations."""
    registrations = (
        Registration.objects
        .filter(user=request.user)
        .select_related('event')
        .order_by('-registered_at')
    )
    return render(request, 'registrations/my_registrations.html', {'registrations': registrations})


@login_required
def participant_list(request, event_id):
    """Staff view of all participants for a specific event."""
    event = get_object_or_404(Event, pk=event_id)

    try:
        # Check permissions: Superuser, Staff, or College Admin
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
    
    attended_count = regs.filter(status='ATTENDED').count()

    return render(request, 'registrations/participant_list.html', {
        'event': event,
        'registrations': regs,
        'attended_count': attended_count,
        'active_count': regs.filter(status='REGISTERED').count(),
        'pending_count': regs.filter(status='PENDING').count(),
        'cancelled_count': regs.filter(status='CANCELLED').count(),
        'total': regs.count(),
    })


@login_required
def approve_registration(request, registration_id):
    """Staff view to approve a pending registration."""
    reg = get_object_or_404(Registration, pk=registration_id)
    
    if not (request.user.is_superuser or request.user.profile.is_staff or getattr(request.user.profile, 'is_admin', False)):
        messages.error(request, 'Permission denied.')
        return redirect('home')

    if reg.status == 'PENDING':
        reg.status = 'REGISTERED'
        reg.save()
        _send_confirmation_email(reg)
        messages.success(request, f"Approved registration for {reg.user.get_full_name() or reg.user.username}.")
    
    return redirect(request.META.get('HTTP_REFERER', 'participant_list'))


@login_required
def reject_registration(request, registration_id):
    """Staff view to reject a pending registration."""
    reg = get_object_or_404(Registration, pk=registration_id)
    
    if not (request.user.is_superuser or request.user.profile.is_staff or getattr(request.user.profile, 'is_admin', False)):
        messages.error(request, 'Permission denied.')
        return redirect('home')

    if reg.status == 'PENDING':
        reg.status = 'CANCELLED'
        reg.save()
        messages.warning(request, f"Rejected registration for {reg.user.get_full_name() or reg.user.username}.")
    
    return redirect(request.META.get('HTTP_REFERER', 'participant_list'))


@login_required
def verify_registration(request, registration_id):
    """Secure endpoint for staff to mark attendance via QR scan or manual click."""
    try:
        if not (request.user.is_superuser or request.user.profile.is_staff or request.user.profile.is_admin):
            messages.error(request, 'Access denied.')
            return redirect('home')
    except Exception:
        return redirect('home')

    registration = get_object_or_404(Registration, pk=registration_id)
    
    if request.method == 'POST':
        if registration.status == 'REGISTERED':
            registration.status = 'ATTENDED'
            registration.save()
            messages.success(request, f"Confirmed! {registration.user.get_full_name() or registration.user.username} marked as Attended.")
        elif registration.status == 'ATTENDED':
            messages.info(request, "Attendance already verified.")
        elif registration.status == 'PENDING':
            messages.warning(request, "Error: This registration is still pending approval.")
        elif registration.status == 'CANCELLED':
            messages.error(request, "Error: This registration was cancelled.")

    return render(request, 'registrations/verify_success.html', {
        'registration': registration,
        'event': registration.event,
        'student': registration.user,
    })


@login_required
def scanner_view(request):
    """Renders the QR camera scanner interface for staff."""
    if not (request.user.is_superuser or request.user.profile.is_staff or getattr(request.user.profile, 'is_admin', False)):
        messages.error(request, 'Access denied. Staff only.')
        return redirect('home')
    return render(request, 'registrations/scanner.html')
