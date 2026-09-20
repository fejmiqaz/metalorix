from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import IdeaNotification, SubmissionBucket
from core.notifications import deliver


class Command(BaseCommand):
    help = 'Retry up to 20 pending owner notifications and prune expired spam counters.'

    def handle(self, *args, **options):
        SubmissionBucket.objects.filter(expires_at__lt=timezone.now()).delete()
        ids = list(IdeaNotification.objects.filter(status='pending', attempts__lt=3).order_by('pk').values_list('pk', flat=True)[:20])
        for pk in ids:
            deliver(pk)
        self.stdout.write('Notification retry pass complete. Check statuses in the admin.')
