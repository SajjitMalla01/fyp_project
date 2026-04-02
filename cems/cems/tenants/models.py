from django.db import models
from django.utils import timezone
import uuid


class College(models.Model):
    """
    Represents a college/institution that uses CEMS.
    Each college is a tenant — isolated data, own branding, own users.
    """
    STATUS_CHOICES = [
        ('ACTIVE',    'Active'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
    ]

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length=200, unique=True)
    slug          = models.SlugField(max_length=100, unique=True,
                                     help_text='Used in URLs: cems.app/college-slug/')
    domain        = models.CharField(max_length=200, blank=True,
                                     help_text='Custom domain if any, e.g. events.herald.edu.np')
    logo_url      = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default='#2563eb',
                                     help_text='Hex color for branding')
    accent_color  = models.CharField(max_length=7, default='#7c3aed')
    address       = models.TextField(blank=True)
    website       = models.URLField(blank=True)
    email         = models.EmailField(blank=True, help_text='College contact email')
    phone         = models.CharField(max_length=20, blank=True)

    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'College'
        verbose_name_plural = 'Colleges'

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return self.status == 'ACTIVE'

    def get_event_count(self):
        return self.events.filter(status='PUBLISHED').count()

    def get_user_count(self):
        return self.profiles.count()
