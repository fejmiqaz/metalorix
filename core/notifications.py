import logging
import json
from urllib.request import Request, urlopen
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from .models import IdeaNotification

logger = logging.getLogger(__name__)


def send_owner_email(subject, body):
    if settings.IDEA_EMAIL_PROVIDER == 'resend':
        if not settings.RESEND_API_KEY:
            raise ValueError('RESEND_API_KEY is missing')
        payload = json.dumps({'from': settings.DEFAULT_FROM_EMAIL,
                              'to': [settings.IDEA_NOTIFICATION_EMAIL], 'subject': subject, 'text': body}).encode()
        request = Request('https://api.resend.com/emails', data=payload, headers={
            'Authorization': f'Bearer {settings.RESEND_API_KEY}', 'Content-Type': 'application/json',
            'User-Agent': 'metalorix/1.0'})
        with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
            result = json.load(response)
        if not isinstance(result, dict) or not result.get('id'):
            raise RuntimeError('Email provider did not accept message')
        return 1
    if settings.IDEA_EMAIL_PROVIDER != 'django':
        raise ValueError('Unsupported IDEA_EMAIL_PROVIDER')
    return send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                     [settings.IDEA_NOTIFICATION_EMAIL], fail_silently=False)


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
        sent = send_owner_email(f'metalorix: new idea #{idea.pk}', body)
        if sent != 1:
            raise RuntimeError('No message accepted')
    except Exception:
        # Keep user data and mail credentials out of logs; saved ideas survive outages.
        logger.warning('Idea notification %s failed; inspect email configuration.', notification_id)
        state = 'failed' if notification.attempts >= 3 else 'pending'
    else:
        state = 'sent'
    IdeaNotification.objects.filter(pk=notification_id).update(status=state, updated_at=timezone.now())
