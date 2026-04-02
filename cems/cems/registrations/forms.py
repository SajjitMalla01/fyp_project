from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import random
from django.core.mail import send_mail
from django.conf import settings

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'autocomplete': 'username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False  # Deactivate until email verified
        
        if commit:
            user.save()
            # Create verification code
            verification_code = str(random.randint(100000, 999999))
            # Save verification code (you need to create this model)
            from accounts.models import EmailVerification
            EmailVerification.objects.create(
                user=user,
                verification_code=verification_code
            )
            # Send verification email
            self.send_verification_email(user, verification_code)
        return user
    
    def send_verification_email(self, user, code):
        subject = 'Verify Your CEMS Account'
        message = f"""
        Welcome to College Event Management System!
        
        Your verification code is: {code}
        
        Please enter this code to activate your account.
        
        Thank you,
        CEMS Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )