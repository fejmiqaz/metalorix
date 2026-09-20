# metalorix

A Django version of the original metalorix page, with its cream (`#f6f0e4`), panel (`#ede2cd`), brown (`#34241e`) and clay (`#a9673a`) palette. Includes a responsive homepage, three newest Instagram posts, private idea submissions with reference images, and an admin studio.

## 1. View it on your computer

Open PowerShell in `C:\Users\User\Desktop\metalorix` and run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Visit **http://127.0.0.1:8000/**. Keep the terminal open. Ctrl+C stops the server. Dependencies and the initial database have already been set up in this workspace; normally you only need the last command.

If setting up on another computer, create the environment first with `py -3.13 -m venv .venv`. No activation is necessary with these commands. Local development uses SQLite and needs no cloud accounts. `.env` is optional locally; copy `.env.example` to `.env` when adding credentials. Never commit `.env`.

## 2. Review submitted ideas

Visitors now enter a name and email with each idea. Email addresses are trimmed and lowercased to group repeat submissions. These are self-reported details, not verified identities. The first submitted name is kept; you can correct it in the admin. Two people using the same email are treated as one sender.

In the admin, **Senders** lists each sender's name, private email and total ideas; click **View ideas** to see just their submissions. **Ideas** is sorted by sender name, then email, with their newest ideas first. You can filter or search by sender and sort by submission count. Existing anonymous ideas are preserved with no sender; their identity cannot be recovered retroactively.

In a second terminal:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Choose your username and password, then visit **http://127.0.0.1:8000/admin/**. Open Ideas to see titles, songs, descriptions and image previews. Mark ideas New, Reviewed, or Inspired a post. Images are accessible only to staff who can view ideas; submissions are never displayed publicly. A submission accepts up to three optional JPEG/PNG/WebP images, 2 MB and 16 megapixels each. Images are resized, re-encoded as JPEG and stripped of metadata.

Small image references are stored directly in the database for a simple initial deployment. This avoids Render's ephemeral filesystem. Watch Neon storage usage and delete old submissions; move to private object storage if volume grows. A one-minute session cooldown and honeypot discourage basic spam; they are not robust abuse prevention. Before a broad public launch, configure edge request-size/rate limits and consider a CAPTCHA. Session cookies can be reset to bypass the cooldown.

## 3. Connect the Instagram feed

Until connected, the latest section shows a link to the Instagram profile. The old hard-coded archive links have been removed. Instagram embeds need internet access and may be blocked by browser privacy settings; each synced post has a direct link fallback.

Use Meta's **Instagram API with Instagram Login** for a **Business or Creator** account. Create a Meta developer app, configure Instagram Login, authorize the metalorix account with the `instagram_business_basic` permission, and obtain its Instagram user ID and access token. Follow the current dashboard requirements for tester roles, review and going live. Do not use the retired Basic Display API or scrape Instagram.

Add to your private `.env`:

```dotenv
INSTAGRAM_ACCESS_TOKEN=your-token
INSTAGRAM_USER_ID=your-instagram-user-id
INSTAGRAM_API_VERSION=v25.0
```

Confirm the supported Graph API version in your Meta app and change `INSTAGRAM_API_VERSION` if needed. Then run:

```powershell
.\.venv\Scripts\python.exe manage.py sync_instagram
```

Refresh the homepage. The command fetches 25 recent media records, orders them by Instagram publication timestamp (not pinned profile order), and atomically keeps only the newest three. Each new post pushes out the oldest of the three. Subsequent syncs replace the snapshot so deletions are reflected. A failed sync leaves the previous feed intact. Credentials stay server-side. The live connection cannot be verified until your account credentials are configured.

The Render Blueprint now includes a cron job scheduled every five minutes. This is polling: new posts appear on page load after the next successful sync, not instantly in already-open tabs. Locally, run the sync command again to update the feed. Token renewal is not automated in this starter; refresh/replace tokens per Meta's current instructions and monitor failed cron runs. You can also manage posts manually in the admin, but the next sync replaces that snapshot.

Official setup: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/

## 4. Deploy later: Render + Neon

Nothing has been deployed or purchased. The included `render.yaml` selects a **paid Starter web service**, supporting the pre-deploy migration command. Review pricing before creating it. It does not create a Render database; the database will be Neon.

1. Push this project to your chosen GitHub repository/branch. Do not commit `.env`, `.venv` or `db.sqlite3`. Your existing GitHub Pages deployment stays separate until you switch your domain. This local repository currently has no remote configured.
2. Create a Neon PostgreSQL project. Copy its connection string from Connect, including `sslmode=require` (and any other supplied security parameters). A pooled connection is supported; server-side cursors are disabled and persistent connections are off.
3. In Render, create a Blueprint from the repository containing `render.yaml`. Set `DATABASE_URL` to the Neon connection string. A production secret key is generated by the Blueprint.
4. Set `ALLOWED_HOSTS` to the eventual Render hostname (without `https://`) and any custom domains, separated by commas. Render's automatic `RENDER_EXTERNAL_HOSTNAME` is also accepted. Set `CSRF_TRUSTED_ORIGINS` to the matching full HTTPS origins, e.g. `https://metalorix.onrender.com,https://metalorix.site`. Use your actual assigned hostname.
5. Enter Instagram credentials, or leave them blank initially. Keep `DEBUG=False`. The build installs dependencies and collects static assets; pre-deploy applies migrations; Gunicorn serves the app. WhiteNoise serves CSS.
6. In the Render service shell run `python manage.py createsuperuser`. Visit `/admin/` on the deployed site. SQLite test ideas are not automatically copied to Neon.
7. The Blueprint includes **metalorix-instagram-sync**, running `python manage.py sync_instagram` every five minutes. Supply the **same Neon DATABASE_URL** and Instagram credentials to both services. Set the same API version if overriding the default. The cron job has its own generated secret key and `DEBUG=False`. Cron jobs incur a separate charge; see https://render.com/docs/cronjobs. After the web service has applied migrations, trigger the cron job once and check its logs. Suspend the cron job until credentials are ready to avoid repeated failures. Do not create a second job if the Blueprint already created it.
8. Confirm forms, admin images and feed syncing on the Render URL. Then add your custom domain in Render and update DNS as Render instructs. Only switch away from GitHub Pages once the new app works.

References: https://render.com/docs/deploy-django and https://neon.com/docs/guides/django

## Checks

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

Tests cover sender grouping and counts, required identity fields, newest-first selection, empty feed, private images, valid and invalid submissions, CSRF, cooldown, idempotent sync, replacing the oldest post and retaining posts on API failure. Live Instagram, Neon and Render verification requires your credentials and deployment.
