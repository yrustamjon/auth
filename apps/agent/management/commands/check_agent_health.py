from django.core.management.base import BaseCommand
from apps.agent.telemetry import detect_missing


class Command(BaseCommand):
    help='Record missing agent connections; run once per minute using a scheduler.'
    def handle(self,*args,**options):
        detect_missing()
        self.stdout.write('Agent health checked.')
