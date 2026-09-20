# metalorix Django app

## Run locally

In PowerShell, from `C:\Users\User\Desktop\metalorix`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/. Create an admin account with `manage.py createsuperuser` using the same Python executable, then open `/admin/`.

Senders shows names, private emails, submission totals, and links to their ideas. Ideas are sorted by sender. Email groups submissions but is self-reported, not verified. Legacy anonymous ideas remain intact. Images remain private to authorized staff and are stored in the database, so Render redeploys do not erase them.

## Instagram: manual archive again

The original three embedded posts are restored when no posts have been entered in the admin. You may manually add posts under Instagram posts (use a unique ID, permalink and publication date); the three newest manual entries appear. The section is labeled as an archive, not a live feed. No Instagram credentials are needed, and the Render sync job has been removed. The old sync command remains dormant for possible future use and is never called automatically.

## Optional owner email notifications

Notifications are disabled by default. They notify **you**, not the submitter, and do not verify the sender's identity. Copy `.env.example` to `.env` and configure:

```dotenv
IDEA_NOTIFICATIONS_ENABLED=True
IDEA_NOTIFICATION_EMAIL=your-owner-address@example.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-provider-smtp-host
EMAIL_PORT=587
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password-or-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your-verified-sending-address@example.com
SITE_URL=http://127.0.0.1:8000
```

Use your provider's verified sender and SMTP credentials. Do not put credentials in Git or chat. Restart the server after changing `.env`. For a local preview without sending real emails, select `django.core.mail.backends.console.EmailBackend`; the message prints in the server terminal. Set `IDEA_NOTIFICATIONS_ENABLED=False` to stop notifications. Use your real HTTPS domain for SITE_URL in production.

Accepted ideas create an outbox record in the same transaction, then attempt delivery after the transaction commits. Only the configured owner receives the message; user-controlled emails are never used as recipients or From headers. Messages contain the sender, title, song, description and a private admin link, without image attachments.

Review Idea notifications in the admin. SMTP failures do not lose the submission. Retry pending messages with:

```powershell
.\.venv\Scripts\python.exe manage.py send_idea_notifications
```

This command retries at most 20 pending messages per run, with at most three attempts each, and removes expired spam counters. Schedule it hourly on your deployment if automatic retries/cleanup are needed; no scheduler has been created. Successful messages are not resent. A worker interrupted during sending stays marked Sending: investigate delivery with the mail provider before resetting it, because SMTP cannot guarantee exactly-once delivery after an ambiguous connection failure. Sent means the backend accepted the message, not guaranteed inbox delivery; console mode is only a preview.

## Spam and flood controls

Database-backed counters are shared by all workers and survive cleared cookies and restarts:

- At most 10 POST attempts per IP per 10-minute window, including invalid submissions.
- At most 120 POST attempts site-wide per minute, checked before form/image parsing.
- At most 5 accepted submissions per IP per hour and 3 per normalized email per day.
- At most 50 accepted submissions site-wide per day, limiting owner notification volume.
- Repeated email + title + song + description combinations are blocked within a daily window, even if images change.
- Existing one-minute browser-session cooldown, honeypot and CSRF checks remain.
- Requests declaring over 7 MB are rejected early. Images are limited to three, each 2 MB/16 megapixels, decoded, resized and re-encoded.

Counters use fixed time windows, so adjacent windows can allow a burst. IP/email keys are stored as secret-keyed hashes. IP limits use the direct peer address and deliberately ignore untrusted forwarding headers. Behind a proxy, visitors may share this address and quota: before public rollout, configure per-visitor rate limiting at the trusted edge and verify its client IP behavior. Do not blindly trust X-Forwarded-For.

Production (`DEBUG=False`) requires Cloudflare Turnstile verification. Create a Turnstile widget for your exact domain(s) and configure:

```dotenv
TURNSTILE_SITE_KEY=your-public-site-key
TURNSTILE_SECRET_KEY=your-private-secret-key
```

The widget token is checked server-side, including the hostname and action. Missing/invalid tokens and verification outages reject submissions. Local development skips Turnstile unless `TURNSTILE_REQUIRED=True`. Production never bypasses it through that setting. No live Turnstile or SMTP verification has occurred yet because credentials are not configured.

These are submission-abuse controls, not a guarantee against DDoS. Before exposing the form publicly, use hosting/edge protections for connection limits, request-rate limits and a 7 MB body limit (including chunked requests). Application checks run only after traffic reaches the server. Distributed attackers can exhaust a global quota; adjust limits for legitimate traffic and monitor rejections. Public GET traffic also needs edge protection.

References: https://developers.cloudflare.com/turnstile/get-started/server-side-validation/ and https://docs.djangoproject.com/en/5.2/topics/email/

## Render + Neon later

Nothing has been deployed. `render.yaml` defines one paid Starter web service; no Instagram cron job or Render database is created.

1. Push the project to your chosen repository. Never commit `.env`, `.venv`, `db.sqlite3` or secrets.
2. Create a Neon PostgreSQL database and copy its connection string, including `sslmode=require` and other supplied security parameters.
3. Create a Render Blueprint from this repository. Set DATABASE_URL to Neon. The Blueprint generates SECRET_KEY and sets DEBUG=False.
4. Set ALLOWED_HOSTS to your domain names (no scheme), and CSRF_TRUSTED_ORIGINS to their full HTTPS origins. Render's automatic hostname is also accepted.
5. Configure Turnstile and the email settings above in Render's environment. Keep notifications off if mail is not ready. Without Turnstile keys the public site loads but idea submissions are rejected.
6. The build installs packages and collects static files. Pre-deploy applies migrations. Gunicorn serves the app. Create your admin account in Render's shell.
7. Test the public form, rate limits, admin image permissions and real mail delivery before pointing the custom domain to Render. Local SQLite records are not copied to Neon automatically.

## Checks

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Tests cover sender grouping, images, CSRF, duplicate/cross-session protection, quotas, owner-only notification delivery, bounded retries and Turnstile validation. SMTP, Turnstile and hosting need live configuration and validation before public launch.
