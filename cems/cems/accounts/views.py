from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

from accounts.forms import UserRegisterForm
from accounts.models import Profile, EmailVerification


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_college_from_session(request):
    """Return the College object from session or fall back to first active one."""
    from tenants.models import College
    college_id = request.session.get('college_id')
    if college_id:
        try:
            return College.objects.get(id=college_id, status__in=['ACTIVE'])
        except College.DoesNotExist:
            pass
    return College.objects.filter(status__in=['ACTIVE']).first()


def _redirect_by_role(user):
    """Redirect authenticated user to their role-specific dashboard."""
    if user.is_superuser:
        return redirect('admin_dashboard')
    try:
        role = user.profile.role
    except Profile.DoesNotExist:
        Profile.objects.get_or_create(user=user, defaults={'role': 'STUDENT'})
        role = 'STUDENT'
    if role == 'ADMIN':
        return redirect('admin_dashboard')
    elif role == 'STAFF':
        return redirect('staff_dashboard')
    return redirect('student_dashboard')


def _send_verification_email(user, code):
    """
    Send a professional HTML verification email.
    """
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    subject = 'Your CEMS Verification Code'
    context = {
        'user': user,
        'code': code,
    }
    
    html_message = render_to_string('emails/verify_email.html', context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"[CEMS EMAIL] Verification code sent to {user.email}")
        return True
    except Exception as exc:
        print(f"[CEMS EMAIL ERROR] Could not send to {user.email}: {exc}")
        print(f"[CEMS EMAIL FALLBACK] Code for {user.username}: {code}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────────────────────────────────────

def register(request, college_slug=None):
    """Register a new user, link to college, send OTP email."""
    from tenants.models import College
    req_college = None
    if college_slug:
        req_college = get_object_or_404(College, slug=college_slug)

    # Check for authentication conflict
    if request.user.is_authenticated:
        try:
            curr_college = request.user.profile.college
            if req_college and curr_college and req_college.id != curr_college.id:
                messages.warning(request, f"You are currently logged in as a member of {curr_college.name}. Please logout to register with {req_college.name}.")
                return redirect('home')
        except: pass
        return redirect('home')

    from tenants.models import College
    college = None
    if college_slug:
        college = get_object_or_404(College, slug=college_slug)
        request.session['college_id'] = str(college.id)
    else:
        college = _get_college_from_session(request)

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data.get('email')
            user.save()
            
            role = form.cleaned_data.get('role', 'STUDENT')
            # If username is superadmin, ensure superuser status
            if user.username == 'superadmin':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            # Domain-based Multi-tenant detection
            email_domain = user.email.split('@')[-1].lower() if '@' in user.email else ''
            from tenants.models import College
            domain_college = College.objects.filter(domain__icontains=email_domain).first()
            if not domain_college:
                # Fallback to name match for heraldcollege.com -> Herald College
                name_part = email_domain.split('.')[0]
                domain_college = College.objects.filter(name__icontains=name_part).first()

            target_college = form.cleaned_data.get('college') or domain_college or college

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.college = target_college
            
            # Staff accounts require approval
            if role == 'STAFF':
                profile.is_approved = False
            else:
                profile.is_approved = True
                
            profile.save()

            # Generate 6-digit OTP with 30-minute expiry
            code = get_random_string(6, allowed_chars='0123456789')
            expires = timezone.now() + timedelta(minutes=30)
            EmailVerification.objects.update_or_create(
                user=user,
                defaults={
                    'verification_code': code,
                    'is_verified': False,
                    'expires_at': expires,
                }
            )

            email_sent = _send_verification_email(user, code)
            request.session['pending_user_id'] = user.id

            if email_sent:
                messages.success(
                    request,
                    f'Account created! A 6-digit verification code was sent to {user.email}.'
                )
            else:
                messages.info(
                    request,
                    f'Account created! (Email service failed) Your debug code is: {code}'
                )
                # Store code in session as fallback if SMTP fails
                request.session['debug_otp'] = code

            return redirect('verify_email')
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'college': college,
    })


def login_view(request, college_slug=None):
    """Authenticate user and route by role."""
    from tenants.models import College
    
    # Handle college slug from URL
    req_college = None
    if college_slug:
        try:
            req_college = College.objects.get(slug=college_slug)
            request.session['college_id'] = str(req_college.id)
            request.session['college_name'] = req_college.name
        except College.DoesNotExist:
            pass

    if request.user.is_authenticated:
        try:
            curr_college = request.user.profile.college
            if req_college and curr_college and req_college.id != curr_college.id:
                messages.warning(request, f"Access Conflict: You are already logged in as a member of {curr_college.name}. You must logout to sign into {req_college.name}.")
                return redirect('college_portal', slug=req_college.slug)
        except: pass
        return _redirect_by_role(request.user)

    # Handle college selection from GET if coming from gateway
    college_id = request.GET.get('college_id') or request.POST.get('college_id')
    if college_id:
        request.session['college_id'] = college_id
        try:
            college = College.objects.get(id=college_id)
            request.session['college_name'] = college.name
            messages.info(request, f'Logging in for {college.name} administrative portal.')
        except: pass

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            profile, _ = Profile.objects.get_or_create(user=user, defaults={'role': 'STUDENT'})
            
            if not profile.is_approved:
                messages.warning(request, 'Your staff account is pending administrative approval. Please wait for an administrator to activate your access.')
                return redirect('login')
                
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return _redirect_by_role(user)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'accounts/login.html')


def admin_gateway(request):
    """A dual-college portal for administration access."""
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
        
    from tenants.models import College
    colleges = College.objects.filter(status__in=['ACTIVE']).order_by('name')[:2]
    
    # If no colleges exist, let's show a helpful state
    if not colleges.exists():
        messages.info(request, "No colleges found. Please register a college first.")
        
    return render(request, 'accounts/admin_gateway.html', {'colleges': colleges})


@login_required
def switch_college(request, college_id):
    """Allow superadmins to switch their active college context instantly."""
    if not request.user.is_superuser:
        messages.error(request, "Permission denied.")
        return redirect('home')
        
    from tenants.models import College
    college = get_object_or_404(College, id=college_id)
    
    profile = request.user.profile
    profile.college = college
    profile.save()
    
    request.session['college_id'] = str(college.id)
    request.session['college_name'] = college.name
    
    messages.success(request, f"Context switched to {college.name}")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))




def logout_view(request):
    """Log out and redirect to home."""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def verify_email(request):
    """Accept OTP code and verify the user's email."""
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.warning(request, 'No pending verification found. Please log in or register.')
        return redirect('login')

    if request.method == 'POST':
        # Join individual digit inputs or accept single field
        digits = [request.POST.get(f'd{i}', '').strip() for i in range(1, 7)]
        if any(digits):
            entered = ''.join(digits)
        else:
            entered = request.POST.get('verification_code', '').strip()

        try:
            ev = EmailVerification.objects.get(
                user_id=user_id,
                verification_code=entered,
                is_verified=False,
            )
            if ev.is_expired():
                messages.error(request, 'This code has expired. Request a new one.')
                return redirect('resend_verification')

            ev.is_verified = True
            ev.save()

            # Clear debug fallback
            if 'debug_otp' in request.session:
                del request.session['debug_otp']

            from django.contrib.auth.models import User
            user = User.objects.get(pk=user_id)
            
            # If staff, check if they need approval
            if user.profile.role == 'STAFF' and not user.profile.is_approved:
                del request.session['pending_user_id']
                messages.success(request, 'Email verified! Your staff account is now pending administrative approval. You will be able to log in once an admin approves your request.')
                return redirect('login')

            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            del request.session['pending_user_id']
            messages.success(request, 'Email verified! Welcome to CEMS.')
            return _redirect_by_role(user)

        except EmailVerification.DoesNotExist:
            messages.error(request, 'Invalid code. Please check and try again.')

    return render(request, 'accounts/verify_email.html')


def resend_verification(request):
    """Re-send a fresh OTP to the user's email."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(email=email)
            code = get_random_string(6, allowed_chars='0123456789')
            expires = timezone.now() + timedelta(minutes=30)
            EmailVerification.objects.update_or_create(
                user=user,
                defaults={
                    'verification_code': code,
                    'is_verified': False,
                    'expires_at': expires,
                }
            )
            email_sent = _send_verification_email(user, code)
            request.session['pending_user_id'] = user.id

            if email_sent:
                messages.success(request, f'New verification code sent to {email}!')
            else:
                messages.info(request, f'New code (email unavailable): {code}')
                # Store code in session as fallback if SMTP fails
                request.session['debug_otp'] = code

            return redirect('verify_email')

        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')

    return render(request, 'accounts/resend_verification.html')

@login_required
def profile_update(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name', user.last_name)
        user.email      = request.POST.get('email', user.email)
        user.save()

        profile = user.profile
        profile.department = request.POST.get('department', profile.department)
        profile.phone      = request.POST.get('phone', profile.phone)
        profile.bio        = request.POST.get('bio', profile.bio)
        profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'accounts/profile_edit.html')


@login_required
def profile_delete(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('home')
    return render(request, 'accounts/profile_delete_confirm.html')

@login_required
def profile(request):
    """User profile view."""
    user_profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'STUDENT'}
    )
    return render(request, 'accounts/profile.html', {
        'profile': user_profile,
    })


@login_required
def approve_staff(request, user_id):
    """Admin view to approve a pending staff user."""
    if not (request.user.is_superuser or request.user.profile.role == 'ADMIN'):
        messages.error(request, 'Permission denied.')
        return redirect('home')
        
    staff_profile = get_object_or_404(Profile, user_id=user_id, role='STAFF')
    staff_profile.is_approved = True
    staff_profile.save()
    
    messages.success(request, f'Approved staff account: {staff_profile.user.username}')
    return redirect('admin_dashboard')


@login_required
def reject_staff(request, user_id):
    """Admin view to reject/delete a pending staff user."""
    if not (request.user.is_superuser or request.user.profile.role == 'ADMIN'):
        messages.error(request, 'Permission denied.')
        return redirect('home')
        
    staff_profile = get_object_or_404(Profile, user_id=user_id, role='STAFF')
    username = staff_profile.user.username
    staff_profile.user.delete() # Deleting user deletes profile
    
    messages.warning(request, f'Rejected and removed staff account: {username}')
    return redirect('admin_dashboard')
