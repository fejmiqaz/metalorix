import json
from io import BytesIO
from unittest.mock import patch
from django.core import mail
from django.test import TestCase, Client, RequestFactory, override_settings
from .models import Idea, IdeaNotification
from .notifications import deliver
from .protection import consume, verify_human


@override_settings(TURNSTILE_REQUIRED=False, IDEA_NOTIFICATIONS_ENABLED=True,
                   IDEA_NOTIFICATION_EMAIL='owner@example.com', EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                             'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class ProtectionTests(TestCase):
    def data(self, title='An idea'):
        return {'sender_name': 'Alex', 'sender_email': 'alex@example.com', 'title': title,
                'song': 'A song', 'description': 'A feeling'}

    def post(self, data=None, **extra):
        with self.captureOnCommitCallbacks(execute=True):
            return Client().post('/ideas/', data or self.data(), **extra)

    def test_email_once_and_duplicate_rejected_with_new_session(self):
        self.assertEqual(self.post().status_code, 302)
        self.assertEqual(self.post().status_code, 429)
        self.assertEqual(Idea.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['owner@example.com'])
        self.assertIn('/admin/core/idea/', mail.outbox[0].body)
        deliver(IdeaNotification.objects.get().pk)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_daily_limit_even_with_different_ips(self):
        for n in range(3):
            self.assertEqual(self.post(self.data(str(n)), REMOTE_ADDR=f'192.0.2.{n}').status_code, 302)
        self.assertEqual(self.post(self.data('four'), REMOTE_ADDR='192.0.2.99').status_code, 429)
        self.assertEqual(len(mail.outbox), 3)

    def test_ip_limit_cannot_be_bypassed_by_spoofed_header(self):
        for n in range(10):
            self.assertEqual(self.post({'title': 'invalid'}, HTTP_X_FORWARDED_FOR=f'192.0.2.{n}').status_code, 400)
        self.assertEqual(self.post(HTTP_X_FORWARDED_FOR='192.0.2.99').status_code, 429)
        self.assertFalse(IdeaNotification.objects.exists())

    def test_body_limit(self):
        self.assertEqual(self.post(CONTENT_LENGTH=str(8 * 1024 * 1024)).status_code, 413)

    def test_global_limit_and_expiry(self):
        with patch('core.protection.time.time', return_value=120):
            self.assertTrue(consume('test', 'all', 1, 60))
            self.assertFalse(consume('test', 'all', 1, 60))
        with patch('core.protection.time.time', return_value=180):
            self.assertTrue(consume('test', 'all', 1, 60))

    @patch('core.notifications.send_mail', side_effect=OSError('mail unavailable'))
    def test_mail_failure_keeps_idea_and_bounded_retries(self, mocked):
        self.assertEqual(self.post().status_code, 302)
        notification = IdeaNotification.objects.get()
        self.assertEqual(Idea.objects.count(), 1)
        for _ in range(5):
            deliver(notification.pk)
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'failed')
        self.assertEqual(mocked.call_count, 3)

    @override_settings(TURNSTILE_REQUIRED=True, TURNSTILE_SECRET_KEY='secret', TURNSTILE_SITE_KEY='site')
    @patch('core.protection.urlopen')
    def test_turnstile_checks_hostname_action_and_failure(self, mocked):
        request = RequestFactory().post('/ideas/', {'cf-turnstile-response': 'token'})
        for payload, valid in [({'success': True, 'hostname': 'testserver', 'action': 'idea'}, True),
                               ({'success': True, 'hostname': 'evil.example', 'action': 'idea'}, False),
                               ({'success': True, 'hostname': 'testserver', 'action': 'other'}, False),
                               ({'success': False}, False)]:
            mocked.return_value.__enter__.return_value = BytesIO(json.dumps(payload).encode())
            self.assertEqual(verify_human(request), valid)
        mocked.side_effect = OSError('offline')
        self.assertFalse(verify_human(request))
        self.assertEqual(self.post().status_code, 400)
        self.assertFalse(Idea.objects.exists())

    @override_settings(TURNSTILE_REQUIRED=True, TURNSTILE_SITE_KEY='', TURNSTILE_SECRET_KEY='')
    def test_missing_keys_disable_widget_and_submission(self):
        response = self.client.get('/')
        self.assertContains(response, 'temporarily unavailable')
        self.assertNotContains(response, 'challenges.cloudflare.com/turnstile/v0/api.js')
        self.assertEqual(self.post().status_code, 503)
        self.assertFalse(Idea.objects.exists())

    @override_settings(IDEA_EMAIL_PROVIDER='resend', RESEND_API_KEY='test-key')
    @patch('core.notifications.urlopen')
    def test_resend_https_owner_only(self, mocked):
        mocked.return_value.__enter__.return_value = BytesIO(b'{"id":"email-123"}')
        self.assertEqual(self.post().status_code, 302)
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.resend.com/emails')
        self.assertEqual(json.loads(request.data)['to'], ['owner@example.com'])
        self.assertEqual(IdeaNotification.objects.get().status, 'sent')

    @override_settings(IDEA_EMAIL_PROVIDER='resend', RESEND_API_KEY='test-key')
    @patch('core.notifications.urlopen', side_effect=OSError('unavailable'))
    def test_resend_failure_preserves_submission(self, mocked):
        self.assertEqual(self.post().status_code, 302)
        self.assertEqual(IdeaNotification.objects.get().status, 'pending')
        self.assertEqual(Idea.objects.count(), 1)
