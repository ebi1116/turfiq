# TurfIQ Analytics

A production-minded Django business intelligence dashboard for turf owners. It tracks manual bookings, customers and expenses, then generates revenue, growth, occupancy, retention, payment, sport and peak-hour analytics.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
.\run_https.ps1
```

Open `https://127.0.0.1:8000/accounts/login/`. Sign in to the seeded full-access workspace with `demo` / `Demo@12345`, or continue with Google. The local certificate is self-signed, so the browser may show a one-time warning. The demo credentials can be overridden with `DEMO_LOGIN_USERNAME` and `DEMO_LOGIN_PASSWORD`.

## Google OAuth setup

1. In Google Cloud Console, create an OAuth 2.0 Client ID for a **Web application**.
2. Add both local addresses as authorized JavaScript origins:

   - `http://127.0.0.1:8000`
   - `http://localhost:8000`
3. Add this exact authorized redirect URI:

   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback/`

Google compares redirect URIs exactly. The scheme, hostname, port, path, and trailing slash must match the address used to open TurfIQ.

## Local HTTPS development

Install the dependencies and start the development-only HTTPS server:

```powershell
python -m pip install -r requirements.txt
New-Item -ItemType Directory -Force .local-certs | Out-Null
python manage.py runserver_plus 127.0.0.1:8000 --cert-file .local-certs/turfiq.crt --key-file .local-certs/turfiq.key
```

Open `https://127.0.0.1:8000/`. The generated certificate is self-signed, so a
browser warning is expected; proceed only for this local address. The certificate
and private key stay under the git-ignored `.local-certs/` directory. Keep
`DJANGO_DEBUG=1` locally; production HTTPS enforcement remains active when debug
mode is disabled.

4. Configure credentials before starting Django:

```powershell
$env:GOOGLE_OAUTH_CLIENT_ID="your-client-id.apps.googleusercontent.com"
$env:GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
python manage.py runserver
```

For production, replace the origin and callback with the public HTTPS domain. Do not configure a duplicate Google `SocialApp` in Django admin while environment credentials are enabled; allauth requires one configuration source per provider.

On first Google authentication, TurfIQ automatically creates an active Owner, stores the verified email, full name, Google subject ID and profile picture, sets an unusable local password, starts a Django session, and redirects to `/dashboard/`.

## Production configuration

Set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `DATABASE_URL` (PostgreSQL URL). For non-Render deployments, also set `DJANGO_CSRF_TRUSTED_ORIGINS` to the comma-separated HTTPS origins that submit forms. Render's `RENDER_EXTERNAL_HOSTNAME` is automatically added to both the allowed hosts and trusted origins. Static assets can then be collected with `python manage.py collectstatic`.

### Razorpay Premium billing

All non-superuser accounts receive a 30-day free full-feature trial. After the trial, Premium access costs ₹199 for 30 days through a manual Razorpay payment. Configure:

```powershell
$env:RAZORPAY_KEY_ID="rzp_test_..."
$env:RAZORPAY_KEY_SECRET="..."
$env:RAZORPAY_PLAN_ID="plan_..."
$env:RAZORPAY_WEBHOOK_SECRET="a-separate-strong-webhook-secret"
```

Configure the public HTTPS webhook URL as `https://your-domain.example/billing/webhook/` and enable subscription events, particularly authenticated, activated, charged, updated, halted, cancelled, and completed. Superusers bypass the subscription gate.

## Verification

```powershell
python manage.py check
python manage.py test
```
