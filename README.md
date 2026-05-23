# Classroom Feedback API

A Django + Django REST Framework application demonstrating JWT-based authentication
and role-based access control (RBAC) with row-level permission enforcement.

---

## Live Demo

**Base URL:** `https://classroom-feedback-api.up.railway.app`
*(replace with your Railway URL after deploying)*

---

## Demo Accounts

| Role       | Email                  | Password   |
|------------|------------------------|------------|
| Instructor | instructor@demo.dev    | Demo@1234  |
| Student    | student@demo.dev       | Demo@1234  |
| Observer   | observer@demo.dev      | Demo@1234  |

---

## Local Setup

```bash
# 1. Enter the demo-app directory
cd zindua-assessment/demo-app

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the environment file and edit if needed
cp .env.example .env

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Seed demo data
python manage.py seed

# 7. Start the development server
python manage.py runserver
```

---

## API Reference

| Method | Endpoint                              | Who can call it                          |
|--------|---------------------------------------|------------------------------------------|
| POST   | `/api/v1/auth/login/`                 | Anyone — returns access + refresh tokens |
| POST   | `/api/v1/auth/refresh/`               | Anyone with a valid refresh token        |
| GET    | `/api/v1/assignments/`                | All roles (filtered by role)             |
| POST   | `/api/v1/assignments/`                | Instructor only                          |
| POST   | `/api/v1/submissions/`                | Student only, enrolled assignments only  |
| GET    | `/api/v1/submissions/{id}/feedback/`  | Row-level: own data only per role        |
| POST   | `/api/v1/submissions/{id}/feedback/`  | Instructor only, own assignments only    |

### Postman walkthrough

**Step 1 — Login**
```
POST /api/v1/auth/login/
Content-Type: application/json

{ "email": "student@demo.dev", "password": "Demo@1234" }
```

**Step 2 — Use the access token**
```
GET /api/v1/assignments/
Authorization: Bearer <access_token>
```

**Step 3 — Refresh the token**
```
POST /api/v1/auth/refresh/
Content-Type: application/json

{ "refresh": "<refresh_token>" }
```

---

## Teaching Comment Location

The primary teaching comment is in **`classroom/permissions.py`** — the block
at the top of the file before any class definitions. It explains:
- The difference between role-level and row-level authorization
- Why role checks alone are insufficient for the Observer
- The OWASP BOLA vulnerability and how our ObserverLink pattern prevents it

A secondary comment is in **`core/settings.py`** inside the `SIMPLE_JWT` block,
explaining why the database (not the token payload) must be the source of truth
for server-side permission checks.

---

## How to Break This App

### Risk 1 — No token blacklisting on logout

**The problem:** JWTs are stateless. Once issued, the server cannot invalidate
an access token. If a user "logs out" in a frontend, their access token remains
valid until it expires (30 minutes in this config). A stolen token gives an
attacker a 30-minute window of unauthorized access even after the user has
"logged out."

**Production fix:** Enable `rest_framework_simplejwt.token_blacklist` in
`INSTALLED_APPS`. Add a `POST /api/v1/auth/logout/` endpoint that blacklists
the refresh token on logout. Shorten the access token lifetime to 5–10 minutes.
For high-security systems (banking, health), consider opaque tokens with
server-side sessions instead of stateless JWTs.

### Risk 2 — No rate limiting on the login endpoint

**The problem:** `POST /api/v1/auth/login/` accepts unlimited requests. An
attacker can run automated credential-stuffing or brute-force attacks against
all user accounts without any throttling.

**Production fix:** Apply DRF's `AnonRateThrottle` to the login endpoint, or
use `django-axes` to lock accounts after N failed attempts and log attacker IPs.
In cloud deployments, add rate limiting at the gateway level (Cloudflare,
AWS WAF) so throttling applies before requests reach Django.

---

## Deployment (Railway)

1. Push the repo to GitHub (make sure `db.sqlite3` is in `.gitignore`).
2. Create a new Railway project → Deploy from GitHub → select the repo.
3. Set the root directory to `demo-app/`.
4. Add a PostgreSQL plugin.
5. Set these environment variables in Railway:
   ```
   SECRET_KEY=<generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
   DEBUG=False
   ALLOWED_HOSTS=your-app.up.railway.app
   CORS_ALLOW_ALL_ORIGINS=True
   ```
   `DATABASE_URL` is injected automatically by Railway's PostgreSQL plugin.
6. Under Settings → Deploy → Start Command, set:
   ```
   python manage.py migrate && python manage.py seed && gunicorn core.wsgi --log-file -
   ```