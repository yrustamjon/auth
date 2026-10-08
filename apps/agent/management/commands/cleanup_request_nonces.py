from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.agent.models import RequestNonce


class Command(BaseCommand):
    help='Delete expired replay records; schedule at least every five minutes.'

    def handle(self,*args,**options):
        count,_=RequestNonce.objects.filter(expires_at__lt=timezone.now()).delete()
        self.stdout.write(f'Deleted {count} expired request nonces')
