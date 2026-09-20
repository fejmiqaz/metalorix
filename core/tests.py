import json
from io import BytesIO, StringIO
from datetime import timedelta
from unittest.mock import patch
from urllib.error import URLError
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone
from .models import Idea, IdeaImage, InstagramPost, Sender


def photo():
    data = BytesIO()
    Image.new('RGB', (20, 20), 'red').save(data, 'PNG')
    return SimpleUploadedFile('reference.png', data.getvalue(), content_type='image/png')


@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                             'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class SiteTests(TestCase):
    def test_empty_and_latest_three(self):
        self.assertContains(self.client.get('/'), 'Visit our Instagram')
        for i in range(4):
            InstagramPost.objects.create(instagram_id=str(i), permalink=f'https://www.instagram.com/p/test{i}/',
                                         published_at=timezone.now() + timedelta(days=i))
        response = self.client.get('/')
        self.assertEqual([p.instagram_id for p in response.context['posts']], ['3', '2', '1'])
        self.assertNotContains(response, '/p/test0/')

    def test_submission_and_private_image(self):
        result = self.client.post('/ideas/', {'title': 'Night drive', 'song': 'Artist — song',
                                             'sender_name': 'Alex', 'sender_email': 'alex@example.com',
                                             'description': 'Quiet nostalgia.', 'images': [photo(), photo()]})
        self.assertRedirects(result, '/#ideas')
        self.assertEqual(Idea.objects.count(), 1)
        self.assertEqual(IdeaImage.objects.count(), 2)
        self.assertTrue(bytes(IdeaImage.objects.first().data).startswith(b'\xff\xd8'))
        self.assertEqual(self.client.get(f'/idea-images/{IdeaImage.objects.first().pk}/').status_code, 302)
        self.assertEqual(self.client.post('/ideas/', {'title': 'Again'}).status_code, 429)

    def test_invalid_images_are_atomic(self):
        for uploads in [[photo(), SimpleUploadedFile('fake.png', b'not an image')], [photo() for _ in range(4)],
                        [SimpleUploadedFile('large.png', b'x' * (2 * 1024 * 1024 + 1))]]:
            result = self.client.post('/ideas/', {'sender_name': 'Alex', 'sender_email': 'alex@example.com', 'title': 'Test', 'song': 'Song', 'description': 'Mood', 'images': uploads})
            self.assertEqual(result.status_code, 400)
        self.assertFalse(Idea.objects.exists())
        self.assertFalse(Sender.objects.exists())

    def test_repeat_sender_grouping_and_private_counts(self):
        from django.test import Client
        from django.contrib.auth import get_user_model
        data = {'sender_name': 'Alex', 'sender_email': 'Alex@Example.com', 'title': 'First', 'song': 'Song', 'description': 'Mood'}
        self.assertEqual(self.client.post('/ideas/', data).status_code, 302)
        data.update(sender_email='alex@example.com', title='Second')
        self.assertEqual(Client().post('/ideas/', data).status_code, 302)
        self.assertEqual(Sender.objects.count(), 1)
        self.assertEqual(Sender.objects.get().ideas.count(), 2)
        data.update(sender_email='other@example.com', title='Third')
        Client().post('/ideas/', data)
        self.assertEqual(Sender.objects.count(), 2)
        admin = get_user_model().objects.create_superuser(username='owner', password='test-password')
        self.client.force_login(admin)
        response = self.client.get('/admin/core/sender/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(s.total for s in response.context['cl'].result_list), [1, 2])
        sender = Sender.objects.get(email='alex@example.com')
        response = self.client.get(f'/admin/core/idea/?sender__id__exact={sender.pk}')
        self.assertEqual(response.context['cl'].result_count, 2)
        self.assertTrue(all(i.total == 2 for i in response.context['cl'].result_list))
        self.assertNotContains(Client().get('/'), 'alex@example.com')

    def test_sender_details_required(self):
        response = self.client.post('/ideas/', {'title': 'Test', 'song': 'Song', 'description': 'Mood'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('sender_email', response.context['form'].errors)
        self.assertIn('sender_name', response.context['form'].errors)

    def test_required_fields_and_honeypot(self):
        self.assertEqual(self.client.post('/ideas/', {}).status_code, 400)
        self.assertEqual(self.client.post('/ideas/', {'title': 'Test', 'song': 'Song', 'description': 'Mood', 'website': 'spam'}).status_code, 400)
        self.assertFalse(Idea.objects.exists())

    def test_csrf_enforced(self):
        from django.test import Client
        self.assertEqual(Client(enforce_csrf_checks=True).post('/ideas/', {}).status_code, 403)


@override_settings(INSTAGRAM_ACCESS_TOKEN='test-secret', INSTAGRAM_USER_ID='123')
class SyncTests(TestCase):
    @patch('core.management.commands.sync_instagram.urlopen')
    def test_new_post_pushes_oldest_out(self, mock):
        def sync(ids):
            data = [{'id': str(i), 'permalink': f'https://www.instagram.com/p/post{i}/',
                     'timestamp': f'2026-09-{i:02d}T10:00:00+0000'} for i in ids]
            mock.return_value.__enter__.return_value = BytesIO(json.dumps({'data': data}).encode())
            call_command('sync_instagram', stdout=StringIO())
        sync([2, 1, 3])
        self.assertEqual(list(InstagramPost.objects.values_list('instagram_id', flat=True)), ['3', '2', '1'])
        sync([2, 4, 1, 3])
        self.assertEqual(list(InstagramPost.objects.values_list('instagram_id', flat=True)), ['4', '3', '2'])

    @patch('core.management.commands.sync_instagram.urlopen')
    def test_sync_idempotent_and_deleted_post_removed(self, mock):
        InstagramPost.objects.create(instagram_id='old', permalink='https://www.instagram.com/p/old/', published_at=timezone.now())
        payload = {'data': [{'id': 'new', 'permalink': 'https://www.instagram.com/p/new/', 'timestamp': '2026-09-20T10:00:00+0000'}]}
        for _ in range(2):
            mock.return_value.__enter__.return_value = BytesIO(json.dumps(payload).encode())
            call_command('sync_instagram', stdout=StringIO())
        self.assertEqual(list(InstagramPost.objects.values_list('instagram_id', flat=True)), ['new'])
        self.assertNotIn('test-secret', mock.call_args.args[0].full_url)

    @patch('core.management.commands.sync_instagram.urlopen', side_effect=URLError('offline'))
    def test_failure_retains_posts(self, mock):
        InstagramPost.objects.create(instagram_id='old', permalink='https://www.instagram.com/p/old/', published_at=timezone.now())
        with self.assertRaises(CommandError):
            call_command('sync_instagram')
        self.assertEqual(InstagramPost.objects.count(), 1)

    @override_settings(INSTAGRAM_ACCESS_TOKEN='')
    def test_missing_credentials(self):
        with self.assertRaises(CommandError):
            call_command('sync_instagram')
