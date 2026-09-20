from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Check idea configuration without revealing secrets or sending email.'

    def handle(self, *args, **options):
        errors = []
        if settings.TURNSTILE_REQUIRED:
            for key in ['TURNSTILE_SITE_KEY', 'TURNSTILE_SECRET_KEY']:
                if not getattr(settings, key):
                    errors.append(f'{key} is missing.')
        else:
            self.stdout.write('Turnstile is disabled for local development.')
        if settings.IDEA_NOTIFICATIONS_ENABLED:
            try:
                validate_email(settings.IDEA_NOTIFICATION_EMAIL)
                validate_email(settings.DEFAULT_FROM_EMAIL)
            except ValidationError:
                errors.append('Set valid IDEA_NOTIFICATION_EMAIL and DEFAULT_FROM_EMAIL addresses.')
            if settings.IDEA_EMAIL_PROVIDER == 'resend':
                if not settings.RESEND_API_KEY:
                    errors.append('RESEND_API_KEY is missing.')
            elif settings.IDEA_EMAIL_PROVIDER == 'django':
                if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
                    self.stdout.write('Email backend is a preview/test backend; real inbox delivery is not enabled.')
                elif not settings.EMAIL_HOST:
                    errors.append('EMAIL_HOST is missing.')
            else:
                errors.append('IDEA_EMAIL_PROVIDER must be resend or django.')
            if not settings.DEBUG and not settings.SITE_URL.startswith('https://'):
                errors.append('Production SITE_URL must use HTTPS.')
        else:
            self.stdout.write('Owner email notifications are disabled.')
        if errors:
            raise CommandError('\n'.join(errors))
        self.stdout.write(self.style.SUCCESS('Configuration checks passed. Verify real Turnstile and email delivery in the browser.'))
