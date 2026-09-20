import json
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware
from core.models import InstagramPost


class Command(BaseCommand):
    help = 'Keep the newest three Instagram posts. Schedule every five minutes in production.'

    def handle(self, *args, **options):
        if not settings.INSTAGRAM_ACCESS_TOKEN or not settings.INSTAGRAM_USER_ID:
            raise CommandError('Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID in your environment first.')
        query = urlencode({'fields': 'id,caption,permalink,timestamp', 'limit': 25})
        url = f'https://graph.instagram.com/{settings.INSTAGRAM_API_VERSION}/{settings.INSTAGRAM_USER_ID}/media?{query}'
        request = Request(url, headers={'Authorization': f'Bearer {settings.INSTAGRAM_ACCESS_TOKEN}'})
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.load(response)
            if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
                raise ValueError('Invalid media response')
            rows = []
            for item in payload['data']:
                if not isinstance(item, dict):
                    raise ValueError('Invalid media record')
                published = parse_datetime(item['timestamp'])
                link = urlparse(item['permalink'])
                if not published or not is_aware(published) or link.scheme != 'https' or link.hostname not in {'instagram.com', 'www.instagram.com'}:
                    raise ValueError('Invalid post')
                rows.append((item['id'], {'caption': item.get('caption', ''), 'permalink': item['permalink'], 'published_at': published}))
            rows.sort(key=lambda row: (row[1]['published_at'], row[0]), reverse=True)
            rows = rows[:3]
        except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError):
            raise CommandError('Instagram sync failed. Check account, token and API version. Saved posts were retained.') from None
        with transaction.atomic():
            for instagram_id, defaults in rows:
                InstagramPost.objects.update_or_create(instagram_id=instagram_id, defaults=defaults)
            # Replace the recent snapshot so removed posts no longer appear.
            InstagramPost.objects.exclude(instagram_id__in=[row[0] for row in rows]).delete()
        self.stdout.write(self.style.SUCCESS(f'Synced {len(rows)} posts; the newest three appear on the homepage.'))
