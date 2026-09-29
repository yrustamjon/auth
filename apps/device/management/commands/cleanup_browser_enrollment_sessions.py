from django.core.management.base import BaseCommand

from apps.device.browser_enrollment import cleanup_sessions


class Command(BaseCommand):
    help = "Expire pending browser enrollment QR sessions and remove old resolved sessions."

    def handle(self, *args, **options):
        cleanup_sessions()
        self.stdout.write(self.style.SUCCESS("Browser enrollment sessions cleaned up."))
