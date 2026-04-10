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
            return College.objects.get(id=college_id, status__in=['ACTIVE', 'TRIAL'])
        except College.DoesNotExist:
            pass
    return College.objects.filter(status__in=['ACTIVE', 'TRIAL']).first()


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
    Send a beautiful HTML OTP email. Falls back to console on SMTP failure.
    Returns True if email was sent successfully.
    """
    subject = 'Your CEMS Verification Code'
    html_message = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Verify Your CEMS Account</title>
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:'Helvetica Neue',Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 20px">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0"
               style="background:#fff;border-radius:20px;overflow:hidden;
                      box-shadow:0 8px 40px rgba(0,0,0,0.10)">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1e40af 0%,#2563eb 50%,#7c3aed 100%);
                       padding:40px;text-align:center">
              <div style="display:inline-block;width:56px;height:56px;
                          background:rgba(255,255,255,0.15);border-radius:14px;
                          font-size:28px;line-height:56px;margin-bottom:16px">🎓</div>
              <h1 style="color:#fff;margin:0;font-size:28px;font-weight:300;
                         font-style:italic;letter-spacing:-0.02em">CEMS</h1>
              <p style="color:rgba(255,255,255,0.65);margin:6px 0 0;font-size:12px;
                        font-weight:700;letter-spacing:0.12em;text-transform:uppercase">
                College Event Management System
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:48px 48px 32px">
              <h2 style="color:#0f172a;font-size:22px;font-weight:600;
                         margin:0 0 12px">Verify your account</h2>
              <p style="color:#475569;line-height:1.7;margin:0 0 36px;font-size:15px">
                Hi <strong style="color:#0f172a">{user.get_full_name() or user.username}</strong>,<br>
                Enter the 6-digit code below to activate your CEMS account.
              </p>

              <!-- OTP Code Box -->
              <div style="background:linear-gradient(135deg,#f8fafc,#f0f4f8);
                          border:1.5px solid #e2e8f0;border-radius:16px;
                          padding:32px;text-align:center;margin-bottom:32px">
                <p style="color:#64748b;font-size:11px;font-weight:700;
                          letter-spacing:0.12em;text-transform:uppercase;margin:0 0 16px">
                  Your Verification Code
                </p>
                <div style="font-family:'Courier New',Courier,monospace;
                            font-size:42px;font-weight:700;color:#0f172a;
                            letter-spacing:0.5em;padding-left:0.5em">
                  {code}
                </div>
              </div>

              <!-- Warning -->
              <div style="background:#fffbeb;border:1.5px solid #fde68a;
                          border-radius:10px;padding:14px 18px;margin-bottom:32px;
                          display:flex;align-items:flex-start;gap:10px">
                <span style="font-size:18px">⏱</span>
                <p style="color:#78350f;font-size:13px;margin:0;line-height:1.6">
                  This code expires in <strong>30 minutes</strong>.
                  If you didn't create a CEMS account, you can safely ignore this email.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 48px 36px;border-top:1px solid #f1f5f9">
              <p style="color:#94a3b8;font-size:12px;margin:0;line-height:1.6">
                Sent to <strong>{user.email}</strong> · CEMS Platform<br>
                <a href="#" style="color:#2563eb;text-decoration:none">Unsubscribe</a> ·
                <a href="#" style="color:#2563eb;text-decoration:none">Privacy Policy</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    plain_message = (
        f"Hi {user.get_full_name() or user.username},\n\n"
        f"Your CEMS verification code is: {code}\n\n"
        f"This code expires in 30 minutes.\n\n"
        f"If you did not register, ignore this email."
    )

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
            Profile.objects.get_or_create(user=user, defaults={'role': 'STUDENT'})
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
    colleges = College.objects.filter(status__in=['ACTIVE', 'TRIAL']).order_by('name')[:2]
    
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
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            del request.session['pending_user_id']
            messages.success(request, 'Email verified! Welcome to CEMS 🎉')
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
