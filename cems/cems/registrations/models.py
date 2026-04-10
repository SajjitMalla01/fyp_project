from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Registration(models.Model):
    STATUS_CHOICES = [
        ('PENDING',    'Pending Approval'),
        ('REGISTERED', 'Registered'),
        ('CANCELLED',  'Cancelled'),
        ('ATTENDED',   'Attended'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='registrations'  # Enables event.registrations.count() in Event model
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REGISTERED'
    )
    registered_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'event')  # Prevent duplicate registrations
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user.username} → {self.event.title} ({self.status})"