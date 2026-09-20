# Enable verification and owner email on metalorix.site

The integration is implemented in the code. You must deploy these changes and supply your own keys. Do not share secrets in chat or commit them to Git.

## 1. Deploy this code

Commit and push the changed files to the branch your Render service deploys. In Render, wait for the deployment to finish (or use Manual Deploy → Deploy latest commit). Keep the existing DATABASE_URL and SECRET_KEY unchanged. No new database migration is needed for this update.

## 2. Create the Turnstile widget

1. Open https://dash.cloudflare.com/ and sign in.
2. Open Turnstile and choose Add widget.
3. Name it `metalorix ideas`.
4. Add hostname `metalorix.site`. Add `www.metalorix.site` if visitors use it, and your actual Render hostname if you want to test there. Enter hostnames without `https://` or a path.
5. Select Managed mode. Leave pre-clearance off; this form does not need it.
6. Create the widget. Copy its site key and secret key privately.

No DNS migration to Cloudflare is required merely to use Turnstile. The form stays closed until both keys are configured. Keys must belong to the same widget.

Reference: https://developers.cloudflare.com/turnstile/get-started/widget-management/dashboard/

## 3. Set up Resend for email over HTTPS

Render Free blocks outbound SMTP ports 25, 465 and 587. Use the implemented Resend HTTPS integration instead.

1. Sign in at https://resend.com/.
2. In Domains, add `metalorix.site` as a sending domain.
3. Copy the exact DNS records shown by Resend into the DNS provider managing the domain. Add the specified email records; preserve the existing website records and any existing mailbox records. Wait until Resend marks the domain verified.
4. In API Keys, create a key with Sending access scoped to the verified domain if offered. Copy it privately.
5. Use `notifications@metalorix.site` as the From address. Your receiving address can be your normal Gmail, Outlook or other inbox; Resend does not create a mailbox for the From address.

References: https://render.com/docs/free and https://resend.com/docs/dashboard/domains/introduction

## 4. Add Render environment variables

Open https://dashboard.render.com/ → your metalorix web service → Environment. Add or update:

| Key | Value |
| --- | --- |
| DEBUG | False |
| TURNSTILE_SITE_KEY | Your Cloudflare site key |
| TURNSTILE_SECRET_KEY | Your Cloudflare secret key |
| SITE_URL | https://metalorix.site |
| IDEA_NOTIFICATIONS_ENABLED | True |
| IDEA_EMAIL_PROVIDER | resend |
| RESEND_API_KEY | Your Resend sending key |
| IDEA_NOTIFICATION_EMAIL | Your real receiving email address |
| DEFAULT_FROM_EMAIL | notifications@metalorix.site |

Ensure `ALLOWED_HOSTS` includes `metalorix.site` and `CSRF_TRUSTED_ORIGINS` includes `https://metalorix.site`. Preserve other valid hosts/origins already in these comma-separated settings. Include www only if that domain is configured too. Do not replace the Neon connection string or application secret.

Save, rebuild, and deploy. Setting the email provider to resend bypasses SMTP settings and the local console email backend.

Reference: https://render.com/docs/configure-environment-variables

## 5. Verify it works

1. Open https://metalorix.site/#ideas in a fresh browser tab.
2. Confirm the Turnstile widget loads without the unavailable message. If it fails, check matching widget keys and allowed hostnames.
3. Enter your name, email, a unique title, song and description. Complete any verification and submit once.
4. Confirm the success message, the new idea under `/admin/core/idea/`, and the notification in your inbox or spam folder.
5. In `/admin/core/ideanotification/`, Sent means the email provider accepted the message. Check Resend's delivery logs if it did not arrive. Pending means an attempt failed; check keys, domain verification and receiving address.
6. After one minute, try the exact same idea again. It should be rejected and should not create another notification. Avoid repeated tests that exhaust the deliberate limits.

Optional configuration check, wherever the deployment environment is available:

```text
python manage.py check_idea_setup
```

This does not print secrets, send email, or prove live credentials work. Render Free has no dashboard shell; browser testing is sufficient, or temporarily run the check as part of your build after all variables are set.

Rate limits and existing spam protections remain active. IP quotas currently use the direct peer address; behind Render's proxy visitors may share that address. Verify and configure trusted edge visitor rate limits before relying on IP quotas as per-person controls. Email quotas, duplicate checks, the global cap and Turnstile also apply. Application limits do not replace network-level flood protection.
