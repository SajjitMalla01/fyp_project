from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('STAFF',   'Staff'),
        ('ADMIN',   'Admin'),
    ]

    user       = models.OneToOneField(User, on_delete=models.CASCADE)
    college    = models.ForeignKey('tenants.College', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='profiles')
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    department = models.CharField(max_length=100, blank=True, null=True)
    phone      = models.CharField(max_length=15, blank=True, null=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio        = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        college_str = f' @ {self.college.name}' if self.college else ''
        return f'{self.user.username} ({self.get_role_display()}){college_str}'

    @property
    def is_student(self):
        return self.role == 'STUDENT'

    @property
    def is_staff(self):
        return self.role == 'STAFF'

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    def get_college_or_none(self):
        return self.college


class EmailVerification(models.Model):
    user              = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=6)
    is_verified       = models.BooleanField(default=False)
    created_at        = models.DateTimeField(auto_now_add=True)
    expires_at        = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.email} — {"Verified" if self.is_verified else "Pending"}'

    def is_expired(self):
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
class EventComment(models.Model):
    event      = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='comments')
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    text       = models.TextField()
    is_pre_event = models.BooleanField(default=True, help_text='True for thoughts before, False for feedback after')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        type_str = "Thought" if self.is_pre_event else "Feedback"
        return f"{self.user.username} - {type_str} on {self.event.title}"
