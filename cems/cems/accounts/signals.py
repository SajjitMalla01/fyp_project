from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, **kwargs):
    """
    Create a Profile for new users (default STUDENT).
    Never overwrite role or college for existing users.
    """
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={'role': 'STUDENT'}
        )
    else:
        # Save profile only if it already exists — don't create here
        # to avoid overriding role set explicitly elsewhere
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            pass
