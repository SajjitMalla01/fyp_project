from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Event(models.Model):
    STATUS_CHOICES = [
        ('PENDING',   'Pending Review'),
        ('APPROVED',  'Approved'),
        ('PUBLISHED', 'Published'),
        ('REJECTED',  'Rejected'),
        ('DRAFT',     'Draft'),
        ('CANCELLED', 'Cancelled'),
    ]

    CATEGORY_CHOICES = [
        ('music',       'Music'),
        ('academic',    'Academic'),
        ('arts',        'Arts'),
        ('technology',  'Technology'),
        ('sports',      'Sports'),
        ('cultural',    'Cultural'),
        ('workshop',    'Workshop'),
        ('seminar',     'Seminar'),
        ('other',       'Other'),
    ]

    college     = models.ForeignKey('tenants.College', on_delete=models.CASCADE,
                                     related_name='events', null=True, blank=True)
    title       = models.CharField(max_length=200)
    description = models.TextField()
    date_time   = models.DateTimeField()
    end_time    = models.DateTimeField(null=True, blank=True)
    venue       = models.CharField(max_length=200)
    capacity    = models.IntegerField(default=100)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='cultural')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    tags        = models.CharField(max_length=200, blank=True,
                                    help_text='Comma-separated tags, e.g. free,outdoor,annual')
    image       = models.ImageField(upload_to='events/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False,
                                             help_text='Require admin approval for each registration')

    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    # Visual fields
    # Default to empty string to avoid forcing emoji content in templates
    emoji    = models.CharField(max_length=10, default='')
    gradient = models.CharField(max_length=20, default='g-blue')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_registered_count(self):
        return self.registrations.exclude(status='CANCELLED').count()

    def is_full(self):
        return self.get_registered_count() >= self.capacity

    def spots_left(self):
        return max(0, self.capacity - self.get_registered_count())

    def is_upcoming(self):
        return self.date_time > timezone.now()

    def get_tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()] if self.tags else []
