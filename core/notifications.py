import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from .models import IdeaNotification

logger = logging.getLogger(__name__)


def deliver(notification_id):
    if not settings.IDEA_NOTIFICATIONS_ENABLED or not settings.IDEA_NOTIFICATION_EMAIL:
        return
    claimed = IdeaNotification.objects.filter(pk=notification_id, status='pending', attempts__lt=3).update(
        status='sending', attempts=F('attempts') + 1, updated_at=timezone.now())
    if not claimed:
        return
    notification = IdeaNotification.objects.select_related('idea__sender').get(pk=notification_id)
    idea = notification.idea
    link = settings.SITE_URL.rstrip('/') + reverse('admin:core_idea_change', args=[idea.pk])
    body = (f'A new idea was submitted to metalorix.\n\n'
            f'Sender: {idea.sender}\nTitle: {idea.title}\nSong: {idea.song}\n\n'
            f'{idea.description}\n\nReview privately: {link}\n'
            'Images remain in the admin. Sender identity is self-reported.')
    try:
        sent = send_mail(f'metalorix: new idea #{idea.pk}', body, settings.DEFAULT_FROM_EMAIL,
                         [settings.IDEA_NOTIFICATION_EMAIL], fail_silently=False)
        if sent != 1:
            raise RuntimeError('No message accepted')
    except Exception:
        # Keep user data and mail credentials out of logs; saved ideas survive outages.
        logger.warning('Idea notification %s failed; inspect email configuration.', notification_id)
        state = 'failed' if notification.attempts >= 3 else 'pending'
    else:
        state = 'sent'
    IdeaNotification.objects.filter(pk=notification_id).update(status=state, updated_at=timezone.now())
