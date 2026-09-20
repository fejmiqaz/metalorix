import hashlib
import json
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from django.conf import settings
from django.db.models import F
from django.http import HttpResponse
from django.utils.crypto import salted_hmac
from .models import SubmissionBucket


def consume(scope, identity, limit, seconds):
    """Shared, atomic fixed-window counters; raw emails/IPs are not stored."""
    window = int(time.time()) // seconds
    key = salted_hmac('submission-limit', f'{scope}:{identity}:{window}').hexdigest()
    SubmissionBucket.objects.get_or_create(key=key, defaults={
        'expires_at': datetime.fromtimestamp((window + 1) * seconds, timezone.utc)})
    return bool(SubmissionBucket.objects.filter(key=key, count__lt=limit).update(count=F('count') + 1))


def client_ip(request):
    # Never trust arbitrary client-supplied forwarding headers.
    return request.META.get('REMOTE_ADDR', 'unknown')


def reject():
    response = HttpResponse('Too many submissions. Please wait before trying again.', status=429, content_type='text/plain')
    response['Retry-After'] = '600'
    return response


class SubmissionGuardMiddleware:
    """Runs before CSRF's multipart parsing and expensive image validation."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/ideas/' and request.method == 'POST':
            try:
                length = int(request.META.get('CONTENT_LENGTH', '0'))
            except ValueError:
                return HttpResponse(status=400)
            if length > 7 * 1024 * 1024:
                return HttpResponse('Submission too large. Maximum total request size is 7 MB.', status=413)
            if not consume('global-attempt', 'all', 120, 60) or not consume('ip-attempt', client_ip(request), 10, 600):
                return reject()
        return self.get_response(request)


def verify_human(request):
    if not settings.TURNSTILE_REQUIRED:
        return True
    token = request.POST.get('cf-turnstile-response', '')
    if not settings.TURNSTILE_SECRET_KEY or not token or len(token) > 2048:
        return False
    data = urlencode({'secret': settings.TURNSTILE_SECRET_KEY, 'response': token}).encode()
    try:
        with urlopen(Request('https://challenges.cloudflare.com/turnstile/v0/siteverify', data=data), timeout=5) as response:
            result = json.load(response)
        return (isinstance(result, dict) and result.get('success') is True
                and result.get('action') == 'idea'
                and result.get('hostname') == request.get_host().split(':')[0])
    except (OSError, ValueError):
        return False


def reserve_submission(request, cleaned):
    fingerprint = hashlib.sha256(json.dumps([cleaned[k].strip().casefold() for k in
        ['sender_email', 'title', 'song', 'description']], ensure_ascii=False).encode()).hexdigest()
    return (consume('duplicate', fingerprint, 1, 86400)
            and consume('email-day', cleaned['sender_email'], 3, 86400)
            and consume('ip-hour', client_ip(request), 5, 3600)
            and consume('global-day', 'all', 50, 86400))
