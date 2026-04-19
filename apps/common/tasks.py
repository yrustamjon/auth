# tasks.py

from celery import shared_task
from django.utils import timezone
from .models import Organization

from apps.org.models import OrgToken


@shared_task
def generate_daily_tokens():
    for org in Organization.objects.all():

        # eski tokenlarni o‘chirish
        OrgToken.objects.filter(
            org=org,
            is_used=False,
            expires_at__gt=timezone.now()
        ).delete()

        # yangi token yaratish
        OrgToken.objects.create(org=org)

    # expired tokenlarni ham tozalash
    OrgToken.cleanup_expired()